#!/usr/bin/env python3
"""Example: luggage tag with a strap slot, a scored border and a colour band.

    python laser/name-tag/job.py
    python scripts/check_svg.py laser/name-tag/build/job.svg
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# works from the project folder and from a frozen copy in versions/vNNN
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "scripts" / "svgjob.py").exists()) / "scripts"))
from svgjob import Job  # noqa: E402

# ---- parameters (mm) ----
WIDTH = 90
HEIGHT = 50
CORNER = 6
SLOT_W = 4      # strap slot, rounded ends
SLOT_H = 16
SLOT_X = 7
BORDER = 3      # scored border inset
BAND_H = 10     # printed colour band along the bottom
BAND_COLOUR = "#1f7a8c"
MATERIAL = "UNTESTED: pick a material and scrap-test it"

job = Job(WIDTH, HEIGHT)

# printed band, kept inside the scored border
job.print_rect(BORDER + 2, HEIGHT - BORDER - 2 - BAND_H, WIDTH - 2 * (BORDER + 2), BAND_H, fill=BAND_COLOUR)

# scored border
b = BORDER
job.score_path(f"M {b} {b} H {WIDTH - b} V {HEIGHT - b} H {b} Z")

# strap slot: a stadium shape drawn with two arcs
r = SLOT_W / 2
top = (HEIGHT - SLOT_H) / 2 + r
bottom = (HEIGHT + SLOT_H) / 2 - r
job.cut_path(
    f"M {SLOT_X} {top} A {r} {r} 0 0 1 {SLOT_X + SLOT_W} {top} "
    f"V {bottom} A {r} {r} 0 0 1 {SLOT_X} {bottom} Z"
)

# outline last, so the piece stays put until everything else is done
job.cut_rect(0, 0, WIDTH, HEIGHT, r=CORNER)

if __name__ == "__main__":
    print(job.save(HERE / "build" / "job.svg"))
