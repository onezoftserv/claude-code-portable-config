"""Turn text into real-size outlines (mm) from a font file.

Used by make_layout.py. Shapes text with HarfBuzz (kerning, script joins),
returns both true-curve SVG path data and shapely geometry for measuring.
Y grows downwards, like SVG; the baseline of a line is at y = 0.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

CURVE_STEPS = 24


def load_font(path, **axes) -> TTFont:
    font = TTFont(str(path))
    if axes and "fvar" in font:
        font = instancer.instantiateVariableFont(font, axes)
    return font


@dataclass
class Line:
    text: str
    glyphs: list         # (glyph name, x offset, y offset) in font units
    font: TTFont
    geom: object         # shapely geometry, mm, ink left edge at x=0, baseline at y=0
    parts: list          # one geometry per glyph, same coordinates
    width: float         # ink width, mm
    top: float           # ink top (negative: above baseline)
    bottom: float        # ink bottom
    scale: float         # mm per font unit
    x0: float            # ink left edge before shifting, mm
    pieces: int          # separate solid pieces (what you would have to place)

    def path_d(self, x: float = 0.0, y: float = 0.0) -> str:
        """True-curve SVG path data with the ink left edge at x and the baseline at y (mm)."""
        glyph_set = self.font.getGlyphSet()
        pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip(".") or "0")
        for name, ox, oy in self.glyphs:
            t = (self.scale, 0, 0, -self.scale, ox * self.scale - self.x0 + x, -oy * self.scale + y)
            glyph_set[name].draw(TransformPen(pen, t))
        return pen.getCommands()


def _flatten(recording):
    """Recording pen ops -> list of closed rings (font units)."""
    rings, ring, cur = [], [], (0, 0)
    for op, args in recording:
        if op == "moveTo":
            ring, cur = [args[0]], args[0]
        elif op == "lineTo":
            ring.append(args[0]); cur = args[0]
        elif op == "qCurveTo":
            pts = list(args)
            # TrueType implied on-curve points between consecutive off-curve points
            on = pts[-1]
            offs = pts[:-1]
            segs = []
            for i, off in enumerate(offs):
                end = on if i == len(offs) - 1 else ((off[0] + offs[i + 1][0]) / 2, (off[1] + offs[i + 1][1]) / 2)
                segs.append((off, end))
            for off, end in segs:
                for s in range(1, CURVE_STEPS + 1):
                    t = s / CURVE_STEPS
                    ring.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * off[0] + t * t * end[0],
                                 (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * off[1] + t * t * end[1]))
                cur = end
        elif op == "curveTo":
            c1, c2, end = args
            for s in range(1, CURVE_STEPS + 1):
                t = s / CURVE_STEPS
                ring.append(((1 - t) ** 3 * cur[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * end[0],
                             (1 - t) ** 3 * cur[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * end[1]))
            cur = end
        elif op in ("closePath", "endPath"):
            if len(ring) >= 3:
                rings.append(ring)
            ring = []
    return rings


def _glyph_geom(rings):
    """Non-zero style fill: contours wound like the biggest one add, the others cut holes."""
    polys = [Polygon(r) for r in rings]
    polys = [(p, Polygon(r).exterior.is_ccw) for p, r in zip(polys, rings) if p.area > 0]
    if not polys:
        return None
    outer_dir = max(polys, key=lambda pc: pc[0].area)[1]
    solid = unary_union([p.buffer(0) for p, ccw in polys if ccw == outer_dir])
    holes = [p.buffer(0) for p, ccw in polys if ccw != outer_dir]
    return solid.difference(unary_union(holes)) if holes else solid


def layout(font: TTFont, text: str, *, cap_height: float | None = None,
           x_height: float | None = None, tracking: float = 0.0, features=None) -> Line:
    """Shape one line. Size it by cap height or x-height in mm. tracking is extra mm between glyphs."""
    os2 = font["OS/2"]
    upm = font["head"].unitsPerEm
    if cap_height is not None:
        ref = getattr(os2, "sCapHeight", 0) or 0.7 * upm
        scale = cap_height / ref
    else:
        ref = getattr(os2, "sxHeight", 0) or 0.45 * upm
        scale = x_height / ref

    data = io.BytesIO()
    font.save(data)
    hb_font = hb.Font(hb.Face(hb.Blob(data.getvalue())))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, features or {"kern": True, "liga": True})

    glyph_set = font.getGlyphSet()
    order = font.getGlyphOrder()
    glyphs, geoms = [], []
    x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        ox, oy = x + pos.x_offset, pos.y_offset
        glyphs.append((name, ox, oy))
        rec = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(rec)
        g = _glyph_geom([[((px + ox) * scale, -(py + oy) * scale) for px, py in ring]
                         for ring in _flatten(rec.value)])
        if g is not None and not g.is_empty:
            geoms.append(g)
        x += pos.x_advance + tracking / scale
    geom = unary_union(geoms)
    minx, miny, maxx, maxy = geom.bounds
    pieces = len(geom.geoms) if hasattr(geom, "geoms") else 1
    parts = [translate(g, xoff=-minx) for g in geoms]
    return Line(text, glyphs, font, translate(geom, xoff=-minx), parts, maxx - minx, miny, maxy, scale, minx, pieces)


def thin_fraction(geom, width_mm: float) -> float:
    """Share of the area that belongs to features narrower than width_mm."""
    r = width_mm / 2
    opened = geom.buffer(-r, join_style=1).buffer(r, join_style=1)
    return max(0.0, 1 - opened.area / geom.area)


def min_feature(geom, lost=0.03) -> float:
    """Widest nozzle-style width (mm) at which less than `lost` of the area would vanish."""
    best = 0.0
    w = 0.2
    while w <= 6.0:
        if thin_fraction(geom, w) > lost:
            break
        best = w
        w += 0.1
    return round(best, 1)


def polygons(geom):
    """Every separate solid piece of a geometry."""
    return list(geom.geoms) if hasattr(geom, "geoms") else [geom]


def geom_path(geom, dx: float = 0.0, dy: float = 0.0) -> str:
    """SVG path data for a shapely geometry: closed outlines only, holes included (use fill-rule evenodd)."""
    out = []
    for poly in polygons(geom):
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)[:-1]
            out.append("M" + " L".join(f"{x + dx:.3f} {y + dy:.3f}" for x, y in pts) + " Z")
    return " ".join(out)
