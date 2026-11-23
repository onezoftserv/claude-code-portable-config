#!/usr/bin/env python3
"""Welcome sign layout: real-size outlines for the 2 x 4 ft board.

    python printer/boda-janny-alex/design/make_layout.py

Proportions follow the client's reference photo (positions and widths as a
share of the board width). Writes, next to this file:

  layout.svg            the whole board, to scale
  medidas.svg           the same with dimensions
  nombres-metalico.svg  JANNY and ALEX, real size, one closed outline per letter, for the supplier
  letras-negras.svg     the painted 3D-printed lines at their board positions
  preview.png           picture of layout.svg
  medidas.md            sizes and positions of every line

Everything is in mm. Change LINES to move or resize anything.
"""
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import box
from shapely.ops import unary_union

from textgeo import geom_path, layout, load_font, min_feature, polygons

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"

BOARD_W, BOARD_H = 609.6, 1219.2     # 2 ft x 4 ft, portrait
BOARD, GOLD, BLACK = "#ebe4d6", "#b08d57", "#1a1a1a"

PLAYFAIR = load_font(FONTS / "PlayfairDisplay.ttf", wght=400)
GARAMOND = load_font(FONTS / "EBGaramond.ttf", wght=700)
SCRIPT = load_font(FONTS / "LuxuriousScript-Regular.ttf")
FONT_NAMES = {id(PLAYFAIR): "Playfair Display Regular", id(GARAMOND): "EB Garamond Bold",
              id(SCRIPT): "Luxurious Script"}

# `grow` thickens every outline by that many mm per side so thin strokes survive 3D printing.
# key, text, font, size, baseline (mm from the top), colour, grow
LINES = [
    ("bienvenidos", "BIENVENIDOS", GARAMOND, dict(cap_height=14, tracking=3.1), 204, BLACK, 0.15),
    ("a-la-boda-de", "A LA BODA DE", GARAMOND, dict(cap_height=14, tracking=3.1), 234, BLACK, 0.15),
    ("janny", "JANNY", PLAYFAIR, dict(cap_height=95, tracking=2), 441, GOLD, 0.0),
    ("y", "&", GARAMOND, dict(cap_height=17), 488, BLACK, 0.15),
    ("alex", "ALEX", PLAYFAIR, dict(cap_height=95, tracking=2), 612, GOLD, 0.0),
    ("fecha", "Enero 23, 2027", SCRIPT, dict(x_height=28), 778, BLACK, 0.05),
]


def build():
    out = []
    for key, text, font, size, baseline, colour, grow in LINES:
        line = layout(font, text, **size)
        geom = line.geom.buffer(grow, join_style=1) if grow else line.geom
        if colour == GOLD:
            pieces = line.parts                      # one per letter
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
