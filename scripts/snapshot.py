#!/usr/bin/env python3
"""Build, check and freeze a project as the next numbered version, then commit and push.

    python scripts/snapshot.py printer/cable-clip -m "wider tab" [-D cable_d=6] [--dual]
    python scripts/snapshot.py laser/name-tag -m "first draft"

Creates <project>/versions/vNNN/ holding the sources, the generated outputs
(3MF/STL + preview, or SVG) and VERSION.md. Nothing is saved unless the checks
pass. Existing versions are never modified.

  --trailer     extra commit trailer, e.g. --trailer "Co-Authored-By: ..." (repeatable)
  --no-push     commit only
  --no-commit   write the version folder only
  --force       save a version even if the sources match the latest one
"""
from __future__ import annotations

import argparse
import datetime
import filecmp
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_part  # noqa: E402
import check_svg  # noqa: E402

SKIP = {"build", "versions", "__pycache__"}
VERSION_RE = re.compile(r"v(\d{3,})$")


def source_files(project: Path) -> list[Path]:
    """Every file in the project except generated output and old versions."""
    return sorted(
        p for p in project.rglob("*")
        if p.is_file() and not (set(p.relative_to(project).parts[:-1]) & SKIP) and p.suffix != ".pyc"
    )


def versions(project: Path) -> list[Path]:
    root = project / "versions"
    if not root.is_dir():
        return []
    return sorted((d for d in root.iterdir() if d.is_dir() and VERSION_RE.fullmatch(d.name)),
                  key=lambda d: int(d.name[1:]))


def next_name(project: Path) -> str:
    existing = versions(project)
    return f"v{(int(existing[-1].name[1:]) + 1) if existing else 1:03d}"


def same_as_latest(project: Path, sources: list[Path], build_args: list[str]) -> bool:
    existing = versions(project)
    if not existing:
        return False
    latest = existing[-1]
    for src in sources:
        old = latest / src.relative_to(project)
        if not old.is_file() or not filecmp.cmp(src, old, shallow=False):
            return False
    meta = latest / "VERSION.md"
    recorded = re.search(r"^- Build options: `(.*)`$", meta.read_text(encoding="utf-8"), re.M) if meta.exists() else None
    return (recorded.group(1) if recorded else "") == " ".join(build_args)


def run_job(script: Path) -> bool:
    """Run a laser job script and relay what it printed through our own stdout."""
    # Both ends of the pipe must agree on an encoding; the Windows default cannot carry every path.
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    for text in (result.stdout, result.stderr):
        if text.strip():
            print(text.rstrip())
    return result.returncode == 0


def build(project: Path, build_args: list[str]) -> list[Path] | None:
    """Run the project's build and checks. Return the output files, or None on failure."""
    out_dir = project / "build"
    if (project / "part.scad").exists():
        shutil.rmtree(out_dir, ignore_errors=True)
        if build_part.main([str(project), *build_args]) != 0:
            return None
    elif (project / "job.py").exists():
        shutil.rmtree(out_dir, ignore_errors=True)
        if not run_job(project / "job.py"):
            return None
        svgs = sorted(out_dir.glob("*.svg"))
        if not svgs or check_svg.main([str(s) for s in svgs]) != 0:
            return None
    else:
        print(f"ERROR: {project} has neither part.scad nor job.py")
        return None
    return sorted(p for p in out_dir.iterdir() if p.is_file())


def write_version(project: Path, sources, outputs, note: str, build_args) -> Path:
    dest = project / "versions" / next_name(project)
    dest.mkdir(parents=True)
    for src in sources:
        target = dest / src.relative_to(project)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    for out in outputs:
        shutil.copy2(out, dest / out.name)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {project.name} {dest.name}",
        "",
        f"- Date: {stamp}",
        f"- Note: {note}",
        f"- Build options: `{' '.join(build_args)}`",
        "- Checks: passed",
        "- Outputs: " + ", ".join(f"`{o.name}`" for o in outputs),
        "",
        "Printed / cut result (fill in after making it):",
        "",
    ]
    (dest / "VERSION.md").write_text("\n".join(lines), encoding="utf-8")
    return dest


def git(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=check, capture_output=True, text=True)


def commit_and_push(project: Path, version: str, note: str, push: bool, trailers=()) -> int:
    rel = project.resolve().relative_to(ROOT).as_posix()
    git("add", "--", rel)
    if not git("diff", "--cached", "--quiet", "--", rel, check=False).returncode:
        print("nothing to commit")
        return 0
    extra = [arg for t in trailers for arg in ("--trailer", t)]
    git("commit", "-m", f"{rel} {version}: {note}", *extra, "--", rel)
    print(f"committed {rel} {version}")
    if not push:
        return 0
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for delay in (0, 2, 4, 8, 16):
        time.sleep(delay)
        result = git("push", "-u", "origin", branch, check=False)
        if result.returncode == 0:
            print(f"pushed to origin/{branch}")
            return 0
    print(f"PUSH FAILED (the commit is saved locally):\n{result.stderr.strip()}")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project", help="e.g. printer/cable-clip or laser/name-tag")
    ap.add_argument("-m", "--message", required=True, help="what changed in this version")
    ap.add_argument("-D", dest="defines", action="append", default=[], metavar="name=value")
    ap.add_argument("--dual", action="store_true")
    ap.add_argument("--stl", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--trailer", action="append", default=[], metavar="'Key: value'")
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args(argv)

    project = Path(args.project)
    if not project.is_dir():
        print(f"ERROR: {project} is not a folder")
        return 2
    build_args = [a for d in args.defines for a in ("-D", d)]
    build_args += ["--dual"] * args.dual + ["--stl"] * args.stl

    sources = source_files(project)
    if not args.force and same_as_latest(project, sources, build_args):
        print(f"no changes since {versions(project)[-1].name}; nothing saved (use --force to save anyway)")
        return 0

    outputs = build(project, build_args)
    if outputs is None:
        print("NOT SAVED: build or checks failed")
        return 1

    dest = write_version(project, sources, outputs, args.message.strip(), build_args)
    print(f"saved {dest}")
    if args.no_commit:
        return 0
    try:
        return commit_and_push(project, dest.name, args.message.strip(), push=not args.no_push, trailers=args.trailer)
    except subprocess.CalledProcessError as exc:
        print(f"GIT FAILED (the version folder is saved, not committed):\n{exc.stderr.strip()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
