#!/usr/bin/env python3
"""Check a mesh (3MF/STL) is printable on the Bambu Lab X2D.

    python scripts/check_mesh.py printer/my-part/build/part.3mf [--dual]

Fails (exit 1) if the mesh is not watertight, has inverted faces or no volume,
or does not fit the build volume. Needs: pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MACHINES = json.loads((ROOT / "machines.json").read_text(encoding="utf-8"))


def load(path):
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    if mesh.is_empty:
        raise ValueError("no geometry")
    return mesh


def check(path, dual: bool = False):
    """Return (errors, info)."""
    try:
        mesh = load(path)
    except Exception as exc:  # trimesh raises many types
        return [f"cannot load: {exc}"], {}
    errors = []
    size = [float(v) for v in mesh.extents]
    limit = MACHINES["x2d"]["dual_nozzle_mm" if dual else "single_nozzle_mm"]
    info = {
        "size_mm": [round(v, 2) for v in size],
        "triangles": int(len(mesh.faces)),
        "bodies": int(mesh.body_count),
        "min_z": round(float(mesh.bounds[0][2]), 3),
    }
    if not mesh.is_watertight:
        errors.append("not watertight (open edges or non-manifold geometry)")
    elif not mesh.is_winding_consistent:
        errors.append("inconsistent face winding (inverted faces)")
    elif mesh.volume <= 0:
        errors.append("volume is zero or negative")
    else:
        info["volume_cm3"] = round(float(mesh.volume) / 1000, 2)
    # X/Y may be swapped by rotating on the plate; Z may not.
    fits = size[2] <= limit[2] and (
        (size[0] <= limit[0] and size[1] <= limit[1]) or (size[1] <= limit[0] and size[0] <= limit[1]))
    if not fits:
        mode = "dual-nozzle" if dual else "single-nozzle"
        errors.append(f"size {info['size_mm']} mm exceeds the {mode} volume {limit} mm")
    return errors, info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mesh", nargs="+")
    ap.add_argument("--dual", action="store_true", help="check against the smaller dual-nozzle volume")
    args = ap.parse_args(argv)
    failed = False
    for path in args.mesh:
        errors, info = check(path, args.dual)
        print(f"{path}: {info}")
        for e in errors:
            print(f"  ERROR: {e}")
        failed |= bool(errors)
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
