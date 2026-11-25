#!/usr/bin/env python3
"""Bolder trials of the serif names: every outline thickened by a fixed amount per side.

    python printer/boda-janny-alex/design/make_bold_options.py

Each trial is scaled back so the capitals stay CAP tall and still sit on the same baselines.
Writes negrita-<n>.svg (names only, same page as nombres-metalico.svg) and prints the sizes.
Nothing here replaces nombres-metalico.svg; it is for choosing a weight.
"""
from pathlib import Path

from shapely.affinity import scale, translate
from shapely.ops import unary_union

import make_layout
from textgeo import geom_path, min_feature, polygons

HERE = Path(__file__).resolve().parent
CAP = 131.0
GROW = [0.0, 0.5, 1.0, 1.5]        # mm added per side
PAGE_W, PAGE_H = 461.55, 332.19


def main():
    names = [i for i in make_layout.build() if i["colour"] == make_layout.GOLD]
    for n, grow in enumerate(GROW):
        k = CAP / (CAP + 2 * grow)
        pieces = []
        for item in names:
            cx = (item["left"] + item["right"]) / 2
            fat = polygons(unary_union([p.buffer(grow, join_style=2, mitre_limit=3) for p in item["pieces"]]))
            fat = [translate(scale(p, k, k, origin=(cx, item["baseline"])), 0, -grow * k) for p in fat]
            pieces.append(fat)
        everything = unary_union([p for ps in pieces for p in ps])
        x0, y0, x1, y1 = everything.bounds
        dx, dy = (PAGE_W - (x1 - x0)) / 2 - x0, (PAGE_H - (y1 - y0)) / 2 - y0
        body = "".join(f'<path fill="#1f1f1f" fill-rule="evenodd" d="{geom_path(p, dx, dy)}"/>\n' for ps in pieces for p in ps)
        (HERE / f"negrita-{n}.svg").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" '
            f'height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">\n{body}</svg>\n', encoding="utf-8")
        flat = [p for ps in pieces for p in ps]
        gap = min(a.distance(b) for ps in pieces for i, a in enumerate(ps) for b in ps[i + 1:])
        print(f"+{grow} mm per side: {x1 - x0:.1f} x {y1 - y0:.1f} mm, thinnest {min(min_feature(p) for p in flat):.1f} mm, "
              f"{len(flat)} pieces, widths {[round(max(p.bounds[2] for p in ps) - min(p.bounds[0] for p in ps), 1) for ps in pieces]}, "
              f"smallest gap {gap:.1f} mm")


if __name__ == "__main__":
    main()
