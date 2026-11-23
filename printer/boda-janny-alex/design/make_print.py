#!/usr/bin/env python3
"""Write the OpenSCAD shape data for one batch of printed letters and its placement template.

    python printer/boda-janny-alex/design/make_print.py

Takes the outlines from make_layout.py (same sizes, same thickening) and writes
`shapes.scad` into the two print projects next to this one:

  printer/boda-letras-bienvenidos/      the letters, 3 mm tall, hanging from a carrier rail by thin tabs
  printer/boda-plantilla-bienvenidos/   alternative: thin plates with letter-shaped holes

Coordinates are mm; y points up in OpenSCAD, so the layout is flipped here.
"""
from pathlib import Path

from shapely.affinity import scale, translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import make_layout
from textgeo import polygons

HERE = Path(__file__).resolve().parent
PRINTER = HERE.parent.parent
BATCH = ["bienvenidos", "a-la-boda-de", "y"]     # keys from make_layout.LINES
TEXT_LINES = ["bienvenidos", "a-la-boda-de"]     # these share one template plate
CLEARANCE = 0.25      # template hole is this much bigger than the letter, per side
MARGIN = 8.0          # template plate around the letters
NOTCH = 3.0           # centre-line notch size
SIMPLIFY = 0.01

# carrier rail: the letters of a line hang from it, already spaced, and it is cut off after gluing
RAIL_GAP = 3.0        # clear space between the rail and the top of the capitals (room for cutters)
RAIL_H = 2.0          # rail size, top to bottom
RAIL_OVER = 9.0       # how far the frame reaches past the widest line, each side
POST_W = 1.2          # side posts joining the two rails
TAB_W = 0.8           # tab width when a letter has two
TAB_W_SINGLE = 1.2    # tab width when a letter has only one
TAB_SPREAD = 3.0      # two tabs must be at least this far apart
TAB_LEVEL = 0.6       # a spot counts as "top of the letter" within this distance of its highest point


def scad_polygon(poly) -> str:
    pts, paths = [], []
    for ring in [poly.exterior, *poly.interiors]:
        coords = list(ring.coords)[:-1]
        paths.append(list(range(len(pts), len(pts) + len(coords))))
        pts += coords
    points = ",".join(f"[{x:.3f},{y:.3f}]" for x, y in pts)
    return f"  polygon(points=[{points}], paths={paths});\n".replace(" ", "") .replace("polygon(", "  polygon(")


def module(name, geoms) -> str:
    body = "".join(scad_polygon(p) for g in geoms for p in polygons(g) if not p.is_empty)
    return f"module {name}() {{\n{body}}}\n\n"


def flip(geom, x0, y1):
    """Board coordinates (y down) -> plate coordinates (y up), origin at the batch's lower-left."""
    return scale(translate(geom, -x0, -y1), 1, -1, origin=(0, 0))


def plate_with_notches(x0, y0, x1, y1, centre_x):
    plate = box(x0, y0, x1, y1)
    notches = [Polygon([(centre_x - NOTCH, y), (centre_x + NOTCH, y), (centre_x, y + d)])
               for y, d in ((y0, NOTCH), (y1, -NOTCH))]
    return plate.difference(unary_union(notches))


def top_profile(poly, step=0.25):
    """(x, y of the letter's upper outline) sampled across its width; board coordinates, y down."""
    x0, y0, x1, y1 = poly.bounds
    out, x = [], x0 + step
    while x < x1 - step / 2:
        hit = poly.intersection(box(x - 0.01, y0 - 1, x + 0.01, y1 + 1))
        if not hit.is_empty:
            out.append((x, hit.bounds[1]))
        x += step
    return out


def tabs_for(poly, rail_bottom):
    """One or two thin strips from the rail down into the top of the letter."""
    prof = top_profile(poly)
    highest = min(y for _, y in prof)
    xs = [x for x, y in prof if y <= highest + TAB_LEVEL]
    # keep clear of the very ends of a flat top so the tab lands on solid material
    inner = [x for x in xs if xs[0] + 0.6 <= x <= xs[-1] - 0.6] or xs
    if inner[-1] - inner[0] >= TAB_SPREAD:
        spots, width = [inner[0], inner[-1]], TAB_W
    else:
        spots, width = [(inner[0] + inner[-1]) / 2], TAB_W_SINGLE
    lookup = dict(prof)
    out = []
    for x in spots:
        y = lookup[min(lookup, key=lambda px: abs(px - x))]
        out.append(box(x - width / 2, rail_bottom - 0.5, x + width / 2, y + 0.6))
    return out


def rail_for(item, x0, x1, centre_x):
    """Rail above a line, with a V notch on the board's centre line. Returns (rail, bottom y)."""
    bottom = item["top"] - RAIL_GAP
    rail = box(x0, bottom - RAIL_H, x1, bottom)
    d = RAIL_H / 2                      # never cut the rail in two
    notch = Polygon([(centre_x - d, bottom - RAIL_H), (centre_x + d, bottom - RAIL_H), (centre_x, bottom - RAIL_H + d)])
    return rail.difference(notch), bottom


def main():
    items = {i["key"]: i for i in make_layout.build() if i["key"] in BATCH}
    centre = make_layout.BOARD_W / 2

    # ---- letters on a carrier: both text lines in one frame, the "&" on its own short rail ----
    text = [items[k] for k in TEXT_LINES]
    amp = items["y"]
    fx0 = min(i["left"] for i in text) - RAIL_OVER
    fx1 = max(i["right"] for i in text) + RAIL_OVER
    rails, tabs, tab_count = [], [], {}
    rail_tops = []
    for i in text:
        rail, bottom = rail_for(i, fx0, fx1, centre)
        rails.append(rail)
        rail_tops.append(bottom - RAIL_H)
        made = [t for p in i["pieces"] for t in tabs_for(p, bottom)]
        tabs += made
        tab_count[i["key"]] = len(made)
    last_bottom = text[-1]["top"] - RAIL_GAP
    posts = [box(fx0, rail_tops[0], fx0 + POST_W, last_bottom), box(fx1 - POST_W, rail_tops[0], fx1, last_bottom)]

    amp_rail, amp_bottom = rail_for(amp, amp["left"] - 10, amp["right"] + 10, centre)
    amp_tabs = [t for p in amp["pieces"] for t in tabs_for(p, amp_bottom)]
    tab_count["y"] = len(amp_tabs)

    y_low = max(i["bottom"] for i in text)                       # lowest ink of the text frame
    park_dx = (fx0 + fx1) / 2 - centre                           # "&" centred under the frame
    park_dy = y_low + 6 - (amp_bottom - RAIL_H)                  # 6 mm below it

    def place(geom, parked=False):
        g = translate(geom, park_dx, park_dy) if parked else geom
        return flip(g, fx0, y_low + 6 + RAIL_H + RAIL_GAP + (amp["bottom"] - amp["top"])).simplify(SIMPLIFY)

    letters = [place(p) for i in text for p in i["pieces"]] + [place(p, True) for p in amp["pieces"]]
    carrier = [place(g) for g in rails + posts] + [place(amp_rail, True)]
    tab_out = [place(t) for t in tabs] + [place(t, True) for t in amp_tabs]

    whole = unary_union([g.buffer(0.001) for g in letters + carrier + tab_out])
    assert len(polygons(whole)) == 2, f"expected 2 connected assemblies, got {len(polygons(whole))}"

    out = PRINTER / "boda-letras-bienvenidos"
    out.mkdir(exist_ok=True)
    (out / "shapes.scad").write_text(
        "// Generated by printer/boda-janny-alex/design/make_print.py. Do not edit by hand.\n\n"
        + module("letters_2d", letters) + module("carrier_2d", carrier) + module("tabs_2d", tab_out), encoding="utf-8")
    print(f"letters: {len(letters)} pieces on 2 carriers; tabs per line: {tab_count}")
    print(f"text frame: {fx1 - fx0:.1f} mm wide; top edge of the upper rail {rail_tops[0]:.1f} mm from the top of the board; "
          f"left edge {fx0:.1f} mm from the left")
    print(f"& rail: {amp['right'] - amp['left'] + 20:.1f} mm wide; top edge {amp_bottom - RAIL_H:.1f} mm from the top of the board; "
          f"left edge {amp['left'] - 10:.1f} mm from the left")

    # ---- template: one plate for the two text lines, one small plate for the "&" ----------
    def holes(item):
        return [Polygon(p.exterior).buffer(CLEARANCE, join_style=1) for p in item["pieces"]]

    tx0, ty0 = min(i["left"] for i in text) - MARGIN, min(i["top"] for i in text) - MARGIN
    tx1, ty1 = max(i["right"] for i in text) + MARGIN, max(i["bottom"] for i in text) + MARGIN
    plate = plate_with_notches(tx0, ty0, tx1, ty1, centre)
    ax0, ay0, ax1, ay1 = amp["left"] - MARGIN, amp["top"] - MARGIN, amp["right"] + MARGIN, amp["bottom"] + MARGIN
    amp_plate = plate_with_notches(ax0, ay0, ax1, ay1, centre)

    gap = 6.0
    plate_out = flip(plate, tx0, ty1)
    holes_out = [flip(h, tx0, ty1) for i in text for h in holes(i)]
    dy = -(ay1 - ay0) - gap
    dx = (tx1 - tx0) / 2 - (ax1 - ax0) / 2
    amp_plate_out = translate(flip(amp_plate, ax0, ay1), dx, dy)
    amp_holes_out = [translate(flip(h, ax0, ay1), dx, dy) for h in holes(amp)]

    out = PRINTER / "boda-plantilla-bienvenidos"
    out.mkdir(exist_ok=True)
    (out / "shapes.scad").write_text(
        "// Generated by printer/boda-janny-alex/design/make_print.py. Do not edit by hand.\n\n"
        + module("plates_2d", [plate_out.simplify(SIMPLIFY), amp_plate_out.simplify(SIMPLIFY)])
        + module("holes_2d", [h.simplify(SIMPLIFY) for h in holes_out + amp_holes_out]), encoding="utf-8")

    webs = unary_union(holes_out)
    print(f"text template: {tx1 - tx0:.1f} x {ty1 - ty0:.1f} mm; top edge {ty0:.1f} mm from the top of the board; "
          f"left edge {tx0:.1f} mm from the left; holes merged into {len(polygons(webs))} openings")
    print(f"& template: {ax1 - ax0:.1f} x {ay1 - ay0:.1f} mm; top edge {ay0:.1f} mm from the top of the board; "
          f"left edge {ax0:.1f} mm from the left")
    gaps = sorted(a.distance(b) for n, a in enumerate(holes_out) for b in holes_out[n + 1:])
    print(f"narrowest web between two holes: {gaps[0]:.2f} mm")


if __name__ == "__main__":
    main()
