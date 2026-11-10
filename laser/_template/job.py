#!/usr/bin/env python3
"""TEMPLATE: copy this folder, rename it, edit the parameters and drawing.

    python laser/<name>/job.py
    python scripts/check_svg.py laser/<name>/build/job.svg
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# works from the project folder and from a frozen copy in versions/vNNN
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "scripts" / "svgjob.py").exists()) / "scripts"))
from svgjob import Job  # noqa: E402

# ---- parameters (mm) ----
WIDTH = 80
HEIGHT = 50
CORNER = 4
MATERIAL = "3 mm basswood plywood"  # must have a confirmed row in laser/materials.md

job = Job(WIDTH, HEIGHT)
job.cut_rect(0, 0, WIDTH, HEIGHT, r=CORNER)          # red: cut
job.score_line(10, HEIGHT / 2, WIDTH - 10, HEIGHT / 2)  # blue: score
job.print_rect(10, 10, 15, 15, fill="#000000")       # filled: print or engrave

if __name__ == "__main__":
    print(job.save(HERE / "build" / "job.svg"))
