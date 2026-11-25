#!/usr/bin/env python3
"""Welcome sign layout: real-size outlines for the 2 x 4 ft board.

    python printer/boda-janny-alex/design/make_layout.py

Proportions follow the client's reference photo, enlarged 15% and moved down
to suit the taller 24 x 48 in board. Writes, next to this file:

  layout.svg            the whole board, to scale
  medidas.svg           the same with dimensions
  nombres-metalico.svg  JANNY and ALEX, real size, closed outlines, for the supplier
  nombres-metalico.dxf  the same for services that take DXF (needs ezdxf)
  letras-negras.svg     the painted 3D-printed lines at their board positions
  preview.png           picture of layout.svg
  medidas.md            sizes and positions of every line

Everything is in mm. Change LINES to move or resize anything.
"""
from pathlib import Path

from shapely.affinity import scale, translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from textgeo import geom_path, layout, load_font, min_feature, polygons

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"

BOARD_W, BOARD_H = 609.6, 1219.2     # 2 ft x 4 ft, portrait
BOARD, GOLD, BLACK = "#ebe4d6", "#b08d57", "#1a1a1a"

NAMES = load_font(FONTS / "AnticDidone-Regular.ttf")
GARAMOND = load_font(FONTS / "EBGaramond.ttf", wght=700)
SCRIPT = load_font(FONTS / "LuxuriousScript-Regular.ttf")
FONT_NAMES = {id(NAMES): "Antic Didone, redrawn", id(GARAMOND): "EB Garamond Bold",
              id(SCRIPT): "Luxurious Script"}

# `grow` thickens every outline by that many mm per side so thin strokes survive 3D printing.
# key, text, font, size, baseline (mm from the top), colour, grow
# Spacing follows the reference photo (a 24 x 36 in board), measured in inches and enlarged 15%:
# 3.8 in from the small lines to the first name, 1.7 in between the names, with the block
# starting 268 mm from the top so it sits just above the middle of this taller 24 x 48 in board.
# The names use a narrow face so they can be as tall as the reference's without running too wide.
LINES = [
    ("bienvenidos", "BIENVENIDOS", GARAMOND, dict(cap_height=16, tracking=3.6), 284, BLACK, 0.15),
    ("a-la-boda-de", "A LA BODA DE", GARAMOND, dict(cap_height=16, tracking=3.6), 318, BLACK, 0.15),
    ("janny", "JANNY", NAMES, dict(cap_height=131, tracking=1.5), 560, GOLD, 0.0),
    ("y", "&", GARAMOND, dict(cap_height=19.5), 595, BLACK, 0.15),
    ("alex", "ALEX", NAMES, dict(cap_height=131, tracking=1.5), 741, GOLD, 0.0),
    ("fecha", "Enero 23, 2027", SCRIPT, dict(x_height=26), 878, BLACK, 0.1),
]


TOUCH = 0.2           # clearance that reads as "touching", mm
# Letters of a name made slightly narrower (1 = as drawn).
NAME_SQUEEZE = {}
# The same, per letter: the reference has narrow upright letters next to a wide A.
LETTER_SQUEEZE = {"N": 0.83}
# How each letter joins the one before it, left to right:
#   a number  = clear gap in mm (TOUCH = just touching); negative = overlap past touching
#   "stem"    = the two letters share one upright stroke (a ligature): the second letter's own
#               left stroke and its serifs are removed, so the join is one clean stroke
# A name listed here keeps these joins; any other name gets one even gap that makes it as
# wide as the widest joined name.
NAME_JOINS = {"janny": [2, -11, "stem", -9]}
NAME_SMOOTH = 0.9     # joined letters: notches narrower than twice this are filled in, mm


def strokes(part, cap):
    """(left edge, right edge) of each stroke crossing the middle of the letter, left to right."""
    band = part.intersection(box(-1e4, -cap * 0.55, 1e4, -cap * 0.45))
    return sorted((g.bounds[0], g.bounds[2]) for g in polygons(band))


def respace(parts, joins, cap):
    """Letters left to right, each joined to the one before it as `joins` says."""
    parts = sorted(parts, key=lambda g: g.bounds[0])
    out = [parts[0]]
    for part, join in zip(parts[1:], joins):
        if join == "stem":
            l0, l1 = strokes(out[-1], cap)[-1]           # the stroke both letters will share
            r0, r1 = strokes(part, cap)[0]
            moved = translate(part, (l0 + l1) / 2 - (r0 + r1) / 2, 0)
            edge = max(l1, moved.bounds[0] + (r1 - r0)) + 0.01
            moved = moved.difference(box(-1e4, -1e4, edge, 1e4))                 # its own left stroke
            moved = moved.difference(box(-1e4, -cap * 0.2, edge + cap * 0.2, 1e4))  # and that stroke's foot
            out.append(max(polygons(moved), key=lambda g: g.area))
            continue
        clear = max(join, TOUCH)
        lo, hi = -400.0, 400.0                   # shift that makes the clearance equal to `clear`
        for _ in range(40):
            mid = (lo + hi) / 2
            moved = translate(part, mid, 0)
            ahead = moved.bounds[0] > out[-1].bounds[0] + 1
            if ahead and moved.distance(out[-1]) >= clear:
                hi = mid
            else:
                lo = mid
        out.append(translate(part, hi + min(join, 0), 0))
    return out


def smooth(parts):
    """Merge overlapping letters and fill the small notches where their serifs meet."""
    groups = polygons(unary_union(parts))
    closed = [g.buffer(NAME_SMOOTH, join_style=1).buffer(-NAME_SMOOTH, join_style=1) for g in groups]
    return polygons(unary_union(closed))


def slices(part, y):
    """(left edge, right edge) of every stroke the letter has at height y, left to right."""
    cut = part.intersection(box(-1e4, y - 0.05, 1e4, y + 0.05))
    return sorted((g.bounds[0], g.bounds[2]) for g in polygons(cut) if not g.is_empty)


def curved_bridge_a(part, cap):
    """Hand-drawn A: the straight crossbar is replaced by a bridge that sweeps up from the left leg.

    It leaves the thin left leg low down, arches up and levels off into the thick right leg,
    like the A in the reference sign. Drawn at the same weight as the crossbar it replaces.
    """
    x0, y0, x1, y1 = part.bounds
    cx = (x0 + x1) / 2
    column = part.intersection(box(cx - 0.05, y0 - 1, cx + 0.05, y1 + 1))
    bar = max(polygons(column), key=lambda g: g.bounds[1])            # lowest piece on the centre line
    top, bottom = bar.bounds[1], bar.bounds[3]
    weight = bottom - top
    above, below = slices(part, top - 0.6), slices(part, bottom + 0.6)
    hole = Polygon([(above[0][1], top - 0.6), (above[-1][0], top - 0.6),
                    (below[-1][0], bottom + 0.6), (below[0][1], bottom + 0.6)])
    legs = part.difference(hole).buffer(0)

    def leg_centre(height, which):
        seg = slices(part, -height)[which]
        return ((seg[0] + seg[1]) / 2, -height)

    start = leg_centre(cap * 0.25, 0)                                 # low on the thin left leg
    end = leg_centre(cap * 0.39, -1)                                  # into the thick right leg
    dx = end[0] - start[0]
    c1 = (start[0] + dx * 0.16, end[1] - cap * 0.05)                  # spring up from the leg...
    c2 = (start[0] + dx * 0.62, end[1] - cap * 0.09)                  # ...arch over and come down into the right leg
    pts = []
    for n in range(41):
        t = n / 40
        pts.append(tuple((1 - t) ** 3 * start[k] + 3 * (1 - t) ** 2 * t * c1[k]
                         + 3 * (1 - t) * t * t * c2[k] + t ** 3 * end[k] for k in (0, 1)))
    bridge = LineString(pts).buffer(weight / 2, cap_style=1, join_style=1)
    return unary_union([legs, bridge])


def tick(x, y0, y1, wide, narrow):
    """Upright wedge serif at x, from y0 to y1: `wide` where it meets the arm (y0), `narrow` at the tip."""
    return Polygon([(x - wide / 2, y0), (x + wide / 2, y0), (x + narrow / 2, y1), (x - narrow / 2, y1)])


def drawn_e(part, cap):
    """Hand-drawn E, after the E in the reference sign.

    A slim upright with three hairline arms, each ending in a thin upright serif (not a ball):
    the top arm's serif crosses the arm, sticking up past the cap line as much as it hangs down;
    the short middle arm (set above the centre) ends in a serif through the arm; and the long
    bottom arm's serif points up from the base line.
    """
    x0 = part.bounds[0]
    stem = cap * 0.08                    # upright
    hair = cap * 0.021                   # arms
    top_len, mid_len, bot_len = cap * 0.47, cap * 0.30, cap * 0.51   # from the left edge
    mid_y = -cap * 0.62                  # middle arm sits above the centre
    wide, narrow = cap * 0.024, cap * 0.018
    tx, mx, bx = x0 + top_len - wide / 2, x0 + mid_len - wide / 2, x0 + bot_len - wide / 2
    shapes = [
        box(x0, -cap, x0 + stem, 0),
        box(x0, -cap, tx + narrow / 2, -cap + hair),                                        # top arm
        box(x0, -hair, bx + narrow / 2, 0),                                     # bottom arm
        box(x0 + stem, mid_y - hair / 2, mx + narrow / 2, mid_y + hair / 2),                # middle arm
        tick(tx, -cap + hair / 2, -cap + cap * 0.065, wide, narrow),           # top serif, down
        tick(tx, -cap + hair / 2, -cap - cap * 0.055, wide, narrow),           # and as far up
        tick(mx, mid_y, mid_y - cap * 0.05, wide, narrow),               # middle serif, up
        tick(mx, mid_y, mid_y + cap * 0.05, wide, narrow),               # and down
        tick(bx, -hair / 2, -cap * 0.085, wide, narrow),                       # bottom serif, up
    ]
    # soften the inside corners where serifs meet arms, like a bracketed serif
    e = unary_union(shapes)
    return e.buffer(-cap * 0.004, join_style=1).buffer(cap * 0.008, join_style=1).buffer(-cap * 0.004, join_style=1)


def drawn_l(part, cap):
    """Hand-drawn L in the same manner as the E: slim upright, hairline foot, upright wedge serif at its end."""
    x0 = part.bounds[0]
    stem, hair, length = cap * 0.08, cap * 0.021, cap * 0.47
    wide, narrow = cap * 0.024, cap * 0.018
    bx = x0 + length - wide / 2
    l = unary_union([
        box(x0, -cap, x0 + stem, 0),
        box(x0, -hair, bx + narrow / 2, 0),
        tick(bx, -hair / 2, -cap * 0.085, wide, narrow),
    ])
    return l.buffer(-cap * 0.004, join_style=1).buffer(cap * 0.008, join_style=1).buffer(-cap * 0.004, join_style=1)


# Hand-drawn replacements, by letter. Each takes the letter's outline and its cap height.
REDRAWN = {"A": curved_bridge_a, "E": drawn_e, "L": drawn_l}


def width_of(parts):
    return max(p.bounds[2] for p in parts) - min(p.bounds[0] for p in parts)


def spaced_names():
    """Both names at the same width: joined names as specified, the others evenly spaced to match."""
    raw, caps = {}, {}
    for key, text, font, size, _, colour, _ in LINES:
        if colour == GOLD:
            k = NAME_SQUEEZE.get(key, 1)
            caps[key] = size["cap_height"]
            letters = sorted(layout(font, text, **size).parts, key=lambda g: g.bounds[0])
            letters = [REDRAWN[ch](part, caps[key]) if ch in REDRAWN else part for ch, part in zip(text, letters)]
            raw[key] = [scale(part, k * LETTER_SQUEEZE.get(ch, 1), 1, origin=(0, 0)) for ch, part in zip(text, letters)]
    out = {key: (respace(raw[key], joins, caps[key]), joins) for key, joins in NAME_JOINS.items()}
    target = max(width_of(parts) for parts, _ in out.values())
    for key, parts in raw.items():
        if key in out:
            continue
        n = len(parts) - 1
        lo, hi = -20.0, 150.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if width_of(respace(parts, [mid] * n, caps[key])) < target:
                lo = mid
            else:
                hi = mid
        out[key] = (respace(parts, [lo] * n, caps[key]), [round(lo, 1)] * n)
    return out


def build():
    out = []
    names = spaced_names()
    for key, text, font, size, baseline, colour, grow in LINES:
        line = layout(font, text, **size)
        geom = line.geom.buffer(grow, join_style=1) if grow else line.geom
        if colour == GOLD:
            letters, joins = names[key]              # respaced; joined letters become one piece
            pieces = smooth(letters) if key in NAME_JOINS else letters
            geom = unary_union(pieces)
            print(f"{text}: joins {joins}, {len(pieces)} piece(s)")
        else:
            pieces = polygons(geom)                  # joined script letters stay one piece
        # centre on the body of the letters, ignoring descenders and swashes below the baseline
        height = size.get("cap_height") or size["x_height"]
        body = geom.intersection(box(-1e4, -height, 1e4, 0))
        bx0, _, bx1, _ = body.bounds
        dx = BOARD_W / 2 - (bx0 + bx1) / 2
        gx0, gy0, gx1, gy1 = geom.bounds
        out.append(dict(key=key, text=text, font=font, size=size, colour=colour, grow=grow,
                        geom=translate(geom, dx, baseline),
                        pieces=[translate(p, dx, baseline) for p in sorted(pieces, key=lambda g: g.bounds[0])],
                        baseline=baseline, left=gx0 + dx, right=gx1 + dx, top=gy0 + baseline, bottom=gy1 + baseline,
                        thinnest=min(min_feature(p) for p in pieces)))
    return out


def svg(width, height, body, background=None):
    bg = f'<rect width="{width:.2f}" height="{height:.2f}" fill="{background}"/>\n' if background else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.2f}mm" height="{height:.2f}mm" '
            f'viewBox="0 0 {width:.2f} {height:.2f}">\n{bg}{body}</svg>\n')


def paths(item, fill, dx=0.0, dy=0.0):
    return "".join(f'<path id="{item["key"]}-{n}" fill="{fill}" fill-rule="evenodd" d="{geom_path(p, dx, dy)}"/>\n'
                   for n, p in enumerate(item["pieces"], 1))


def dimensions(items):
    """Board drawing with baselines, heights and widths called out."""
    pad_l, pad_r, pad_t, pad_b = 150, 190, 60, 40
    w, h = BOARD_W + pad_l + pad_r, BOARD_H + pad_t + pad_b
    t = lambda x, y, s, anchor="start", size=13, colour="#333": (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" '
        f'fill="{colour}" text-anchor="{anchor}">{s}</text>\n')
    out = [f'<rect x="{pad_l}" y="{pad_t}" width="{BOARD_W}" height="{BOARD_H}" fill="#f4f1ea" stroke="#333" stroke-width="1"/>\n']
    out.append(t(pad_l + BOARD_W / 2, pad_t - 22, f"{BOARD_W:g} mm (24 in)", "middle", 15))
    out.append(t(pad_l + BOARD_W + 12, pad_t + BOARD_H - 8, f"{BOARD_H:g} mm (48 in)", "start", 15))
    out.append(f'<line x1="{pad_l + BOARD_W / 2}" y1="{pad_t}" x2="{pad_l + BOARD_W / 2}" y2="{pad_t + BOARD_H}" '
               f'stroke="#c33" stroke-width="0.6" stroke-dasharray="6 5"/>\n')
    for i in items:
        fill = "#b08d57" if i["colour"] == GOLD else "#555"
        out.append(paths(i, fill, pad_l, pad_t))
        y = i["baseline"] + pad_t
        out.append(f'<line x1="{pad_l - 8}" y1="{y}" x2="{pad_l + BOARD_W + 8}" y2="{y}" stroke="#06c" stroke-width="0.5"/>\n')
        out.append(t(pad_l - 12, y + 4, f'{i["baseline"]:g}', "end", 13, "#06c"))
        height = i["size"].get("cap_height") or i["size"]["x_height"]
        kind = "cap" if "cap_height" in i["size"] else "x-height"
        out.append(t(pad_l + BOARD_W + 12, y + 4, f'{height:g} mm {kind} · {i["right"] - i["left"]:.0f} mm wide', "start", 13))
    out.append(t(pad_l - 12, pad_t - 6, "baseline, mm from top", "end", 11, "#06c"))
    return svg(w, h, "".join(out), "#ffffff")


def main():
    items = build()
    names = [i for i in items if i["colour"] == GOLD]
    black = [i for i in items if i["colour"] == BLACK]

    for a in items:                       # nothing may touch or leave the board
        assert a["left"] > 20 and a["right"] < BOARD_W - 20, a["key"]
        for b in items:
            if a is not b and a["geom"].distance(b["geom"]) < 3:
                raise SystemExit(f'{a["key"]} and {b["key"]} are closer than 3 mm')

    (HERE / "layout.svg").write_text(svg(BOARD_W, BOARD_H, "".join(paths(i, i["colour"]) for i in items), BOARD), encoding="utf-8")
    (HERE / "medidas.svg").write_text(dimensions(items), encoding="utf-8")
    (HERE / "letras-negras.svg").write_text(svg(BOARD_W, BOARD_H, "".join(paths(i, "#000000") for i in black)), encoding="utf-8")

    # supplier file: names only, kept in their relative positions, 10 mm margin
    x0 = min(i["left"] for i in names) - 10
    y0 = min(i["top"] for i in names) - 10
    w = max(i["right"] for i in names) + 10 - x0
    h = max(i["bottom"] for i in names) + 10 - y0
    (HERE / "nombres-metalico.svg").write_text(svg(w, h, "".join(paths(i, "#000000", -x0, -y0) for i in names)), encoding="utf-8")

    # the same names as DXF (mm, y up, closed polylines), for cutting services that do not take SVG
    try:
        import ezdxf
    except ImportError:
        print("nombres-metalico.dxf skipped (pip install ezdxf)")
    else:
        doc = ezdxf.new("R2010")
        doc.units = ezdxf.units.MM
        space = doc.modelspace()
        for i in names:
            for piece in i["pieces"]:
                for ring in [piece.exterior, *piece.interiors]:
                    pts = [(x - x0, h - (y - y0)) for x, y in list(ring.coords)[:-1]]
                    space.add_lwpolyline(pts, close=True)
        doc.saveas(HERE / "nombres-metalico.dxf")

    rows = ["| Line | Font | Letter height | Width | Top to bottom | Baseline from top | Thinnest stroke | Pieces |",
            "|---|---|---|---|---|---|---|---|"]
    for i in items:
        kind = "cap" if "cap_height" in i["size"] else "x-height"
        height = i["size"].get("cap_height") or i["size"]["x_height"]
        grow = f' (after +{i["grow"]:g} mm per side)' if i["grow"] else ""
        rows.append(f'| {i["text"]} | {FONT_NAMES[id(i["font"])]} | {height:g} mm ({kind}) | '
                    f'{i["right"] - i["left"]:.0f} mm | {i["top"]:.0f} to {i["bottom"]:.0f} mm | {i["baseline"]:g} mm | '
                    f'{i["thinnest"]:.1f} mm{grow} | {len(i["pieces"])} |')
    table = "\n".join(rows)
    (HERE / "medidas.md").write_text(
        f"# Medidas\n\nBoard: {BOARD_W:g} x {BOARD_H:g} mm (2 x 4 ft), portrait. Every line is centred on the board.\n"
        f"\"Thinnest stroke\" is the worst piece in the line: the widest feature size that keeps 97% of its area.\n\n"
        f"{table}\n\nSupplier file `nombres-metalico.svg`: {w:.0f} x {h:.0f} mm page, letters at real size and real spacing.\n",
        encoding="utf-8")
    print(table)
    print(f"names page {w:.0f} x {h:.0f} mm; biggest black piece "
          f"{max(max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1]) for i in black for p in i['pieces']):.0f} mm")

    try:
        import cairosvg
        cairosvg.svg2png(url=str(HERE / "layout.svg"), write_to=str(HERE / "preview.png"), output_width=700)
        cairosvg.svg2png(url=str(HERE / "medidas.svg"), write_to=str(HERE / "medidas.png"), output_width=950)
    except ImportError:
        print("PNG previews skipped (pip install cairosvg)")


if __name__ == "__main__":
    main()
