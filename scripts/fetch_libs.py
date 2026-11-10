#!/usr/bin/env python3
"""Fetch the free libraries listed in libs.json into libs/ (gitignored).

    python scripts/fetch_libs.py            # default set
    python scripts/fetch_libs.py --all
    python scripts/fetch_libs.py NopSCADlib tabler-icons
    python scripts/fetch_libs.py --update   # move to latest and rewrite the lock

The first fetch records each commit in libs.lock.json. Commit that file: later
fetches (and other machines) then get exactly the same versions.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ROOT / "libs"
LOCK = ROOT / "libs.lock.json"


def git(*args, cwd=None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fetch(lib: dict, pinned: str | None, update: bool) -> str:
    dest = LIBS / lib["name"]
    if not dest.exists():
        git("init", "-q", str(dest))
        git("remote", "add", "origin", lib["url"], cwd=dest)
    elif pinned and not update and git("rev-parse", "HEAD", cwd=dest) == pinned:
        return pinned
    ref = pinned if pinned and not update else "HEAD"
    git("fetch", "-q", "--depth", "1", "origin", ref, cwd=dest)
    git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=dest)
    return git("rev-parse", "HEAD", cwd=dest)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="library names from libs.json")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--update", action="store_true", help="ignore the lock and take the latest commit")
    args = ap.parse_args(argv)

    libs = json.loads((ROOT / "libs.json").read_text(encoding="utf-8"))["libs"]
    known = {lib["name"] for lib in libs}
    unknown = set(args.names) - known
    if unknown:
        print(f"ERROR: not in libs.json: {', '.join(sorted(unknown))}")
        return 2
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    wanted = [lib for lib in libs if args.all or lib["name"] in args.names
              or (not args.names and lib.get("default"))]

    LIBS.mkdir(exist_ok=True)
    failed = False
    for lib in wanted:
        name = lib["name"]
        try:
            sha = fetch(lib, lock.get(name), args.update)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            print(f"FAILED {name}: {detail.strip()}")
            failed = True
            continue
        lock[name] = sha
        print(f"ok {name} @ {sha[:10]}  ({lib['licence']})")
    LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
