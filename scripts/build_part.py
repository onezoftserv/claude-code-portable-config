#!/usr/bin/env python3
"""Build an OpenSCAD part: mesh + preview image + printability check.

    python scripts/build_part.py printer/cable-clip [-D width=12] [--dual] [--stl]

Reads <project>/part.scad, writes <project>/build/part.3mf (or .stl) and
preview.png, then runs check_mesh.py on the result.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_mesh  # noqa: E402

CANDIDATES = [
    r"C:\Program Files\OpenSCAD\openscad.com",
    r"C:\Program Files\OpenSCAD\openscad.exe",
    r"C:\Program Files\OpenSCAD (Nightly)\openscad.com",
    "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
]


def find_openscad() -> str | None:
    override = os.environ.get("OPENSCAD")
    if override:
        return override
    for name in ("openscad", "openscad-nightly"):
        found = shutil.which(name)
        if found:
            return found
    return next((c for c in CANDIDATES if Path(c).exists()), None)


def run(cmd, env) -> bool:
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    return proc.returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project", help="folder containing part.scad")
    ap.add_argument("-D", dest="defines", action="append", default=[], metavar="name=value")
    ap.add_argument("--dual", action="store_true", help="check against the dual-nozzle volume")
    ap.add_argument("--stl", action="store_true", help="export STL instead of 3MF")
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args(argv)

    project = Path(args.project)
    scad = project / "part.scad"
    if not scad.exists():
        print(f"ERROR: {scad} not found")
        return 2
    openscad = find_openscad()
    if not openscad:
        print("ERROR: OpenSCAD not found. Install it (setup.ps1 does) or set the OPENSCAD env var.")
        return 2

    build = project / "build"
    build.mkdir(exist_ok=True)
    env = dict(os.environ, OPENSCADPATH=str(ROOT / "libs"))
    defines = [arg for d in args.defines for arg in ("-D", d)]
    base = [openscad, "-q", "--hardwarnings", *defines]

    out = build / ("part.stl" if args.stl else "part.3mf")
    print(f"export {out}")
    ok = run([*base, "-o", str(out), str(scad)], env)
    if not ok and not args.stl:
        # OpenSCAD builds without lib3mf cannot write 3MF.
        out = build / "part.stl"
        print(f"3MF export failed, retrying as {out}")
        ok = run([*base, "-o", str(out), str(scad)], env)
    if not ok or not out.exists():
        print("FAILED: OpenSCAD did not produce a mesh")
        return 1

    if not args.no_preview:
        png = build / "preview.png"
        cmd = [*base, "-o", str(png), "--imgsize=1024,768", "--autocenter", "--viewall", "--render=true", str(scad)]
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
            cmd = ["xvfb-run", "-a", *cmd]
        if not run(cmd, env):
            print("  warning: preview image failed (needs a display); mesh is unaffected")

    return check_mesh.main([str(out)] + (["--dual"] if args.dual else []))


if __name__ == "__main__":
    sys.exit(main())
