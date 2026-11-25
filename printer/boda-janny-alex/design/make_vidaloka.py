#!/usr/bin/env python3
"""JANNY / ALEX in Vidaloka: a second version of the supplier file.

    python printer/boda-janny-alex/design/make_vidaloka.py

The letters are Vidaloka exactly as drawn (Google Fonts, OFL), nothing redrawn or joined.
Both names have the same letter height. JANNY is WIDTH wide at its natural spacing; ALEX is
letter-spaced part of the way out to that width (SPREAD) and centred. GAP is the clear space
between JANNY's baseline and the top of ALEX's capitals, sized so the "&" keeps its place on
the board when JANNY's baseline stays at 560 mm.

Writes, next to this file:

  nombres-vidaloka.svg   real size, closed outlines, no text, 10 mm margin
  nombres-vidaloka.dxf   the same for services that take DXF (mm, closed polylines)
  nombres-vidaloka.png   picture of the SVG
"""
from pathlib import Path

from shapely.affinity import translate
from shapely.ops import unary_union

from textgeo import geom_path, layout, load_font, min_feature

HERE = Path(__file__).resolve().parent
FONT = load_font(HERE.parent / "fonts" / "Vidaloka-Regular.ttf")

WIDTH = 480.0        # widest name, mm (the board is 609.6 wide)
GAP = 53.0           # first baseline to the cap top of the second name, mm
MARGIN = 10.0
NAMES = ["JANNY", "ALEX"]
SPREAD = 0.5          # shorter names: 0 = natural letter spacing, 1 = spaced out to the full width


def letters(text, cap, tracking):
    """One shapely outline per letter, ink left edge at x = 0, baseline at y = 0."""
    return sorted(layout(FONT, text, cap_height=cap, tracking=tracking).parts, key=lambda g: g.bounds[0])


def width(parts):
    return max(p.bounds[2] for p in parts) - min(p.bounds[0] for p in parts)


def build():
    # the widest name at its natural spacing sets the letter height...
    natural = {t: width(letters(t, 100.0, 0.0)) for t in NAMES}
    cap = 100.0 * WIDTH / max(natural.values())
    # ...and the others are letter-spaced SPREAD of the way out to that width, then centred
    lines = []
    for text in NAMES:
        lo, hi = 0.0, 200.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if width(letters(text, cap, mid)) < WIDTH:
                lo = mid
            else:
                hi = mid
        parts = letters(text, cap, lo * SPREAD)
        x0 = min(p.bounds[0] for p in parts) - (WIDTH - width(parts)) / 2
        lines.append(dict(text=text, tracking=lo * SPREAD, parts=[translate(p, -x0, 0) for p in parts]))
    # first name's ink top at y = 0, the second name's capitals GAP below the first baseline
    top = min(p.bounds[1] for p in lines[0]["parts"])
    lines[0]["baseline"] = -top
    for prev, line in zip(lines, lines[1:]):
        line["baseline"] = prev["baseline"] + GAP + cap
    for line in lines:
        line["parts"] = [translate(p, MARGIN, MARGIN + line["baseline"]) for p in line["parts"]]
    height = max(p.bounds[3] for p in lines[-1]["parts"]) - MARGIN
    return cap, lines, height


def main():
    cap, lines, height = build()
    w, h = WIDTH + 2 * MARGIN, height + 2 * MARGIN
    body = "".join(
        f'<path id="{line["text"].lower()}-{n}" fill="#000000" fill-rule="evenodd" d="{geom_path(p)}"/>\n'
        for line in lines for n, p in enumerate(line["parts"], 1))
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
           f'viewBox="0 0 {w:.2f} {h:.2f}">\n{body}</svg>\n')
    (HERE / "nombres-vidaloka.svg").write_text(svg, encoding="utf-8")

    import ezdxf
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    space = doc.modelspace()
    for line in lines:
        for piece in line["parts"]:
            for ring in [piece.exterior, *piece.interiors]:
                space.add_lwpolyline([(x, h - y) for x, y in list(ring.coords)[:-1]], close=True)
    doc.saveas(HERE / "nombres-vidaloka.dxf")

    everything = unary_union([p for line in lines for p in line["parts"]])
    x0, y0, x1, y1 = everything.bounds
    print(f"letter height {cap:.1f} mm; ink box {x1 - x0:.2f} x {y1 - y0:.2f} mm; page {w:.2f} x {h:.2f} mm")
    for line in lines:
        ps = line["parts"]
        gaps = [round(b.bounds[0] - a.bounds[2], 1) for a, b in zip(ps, ps[1:])]
        print(f'{line["text"]}: baseline {line["baseline"]:.1f} mm from the ink top, width {width(ps):.1f} mm, '
              f'gaps {gaps}, clear gaps {[round(a.distance(b), 1) for a, b in zip(ps, ps[1:])]}, '
              f'thinnest stroke {min(min_feature(p) for p in ps):.1f} mm, {len(ps)} pieces, '
              f'ink {min(p.bounds[1] for p in ps) - MARGIN:.1f} to {max(p.bounds[3] for p in ps) - MARGIN:.1f}')

    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.replace("<path", '<rect width="100%" height="100%" fill="#ffffff"/>\n<path', 1).encode(),
                         write_to=str(HERE / "nombres-vidaloka.png"), output_width=1200)
    except ImportError:
        print("PNG preview skipped (pip install cairosvg)")


if __name__ == "__main__":
    main()
