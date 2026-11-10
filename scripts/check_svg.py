#!/usr/bin/env python3
"""Validate an SVG laser/print job for the xTool M2. Standard library only.

    python scripts/check_svg.py laser/my-job/build/job.svg [--module laser|ir]

Errors (exit 1):
  - width/height not in mm, or viewBox not 1 unit = 1 mm
  - <text>, <use>, <style> or any transform (keep geometry literal)
  - a cut (red) or score (blue) element that has a fill
  - anything outside the bed, or print artwork larger than the print area
  - duplicate cut/score geometry (the laser would pass twice)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MACHINES = json.loads((ROOT / "machines.json").read_text(encoding="utf-8"))
CUT = MACHINES["svg_roles"]["cut"]
SCORE = MACHINES["svg_roles"]["score"]
SHAPES = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "image"}
BANNED = {"text": "convert text to paths", "use": "inline the geometry", "style": "use plain attributes"}
EPS = 1e-6
NAMED = {"red": "#ff0000", "blue": "#0000ff", "black": "#000000", "white": "#ffffff"}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def colour(value: str | None) -> str | None:
    """Normalise to #rrggbb, or None for 'none'/missing."""
    if value is None:
        return None
    v = value.strip().lower()
    if v in ("", "none", "transparent"):
        return None
    v = NAMED.get(v, v)
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(c * 2 for c in v[1:])
    m = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", v)
    if m:
        v = "#%02x%02x%02x" % tuple(min(255, int(g)) for g in m.groups())
    return v


def own_paint(el) -> dict:
    paint = {}
    for key in ("stroke", "fill"):
        if el.get(key) is not None:
            paint[key] = el.get(key)
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip() in ("stroke", "fill"):
                paint[k.strip()] = v.strip()
    return paint


# ---- geometry ---------------------------------------------------------------
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOKEN = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|(" + NUM.pattern + ")")
ARGS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}


def arc_points(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2, n=24):
    """Sample an SVG elliptical arc (endpoint parameterisation, SVG 1.1 F.6.5)."""
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [(x2, y2)]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg)
    c, s = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    xp, yp = c * dx + s * dy, -s * dx + c * dy
    lam = xp * xp / (rx * rx) + yp * yp / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * yp * yp - ry * ry * xp * xp
    den = rx * rx * yp * yp + ry * ry * xp * xp
    k = math.sqrt(max(0.0, num / den)) if den else 0.0
    if bool(large) == bool(sweep):
        k = -k
    cxp, cyp = k * rx * yp / ry, -k * ry * xp / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2
    t1 = math.atan2((yp - cyp) / ry, (xp - cxp) / rx)
    t2 = math.atan2((-yp - cyp) / ry, (-xp - cxp) / rx)
    dt = t2 - t1
    if sweep and dt < 0:
        dt += 2 * math.pi
    elif not sweep and dt > 0:
        dt -= 2 * math.pi
    pts = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((c * ex - s * ey + cx, s * ex + c * ey + cy))
    return pts


def path_points(d: str):
    """Points whose bounding box contains the path (control points for curves)."""
    pts, cmd, nums = [], None, []
    x = y = sx = sy = 0.0

    def flush():
        nonlocal x, y, sx, sy, nums, cmd
        if cmd is None:
            if nums:
                raise ValueError("path data starts with a number")
            return
        low, rel = cmd.lower(), cmd.islower()
        n = ARGS[low]
        if low == "z":
            x, y = sx, sy
            pts.append((x, y))
            nums = []
            return
        if not nums or len(nums) % n:
            raise ValueError(f"wrong number of values for '{cmd}'")
        for i in range(0, len(nums), n):
            a = nums[i:i + n]
            ox, oy = (x, y) if rel else (0.0, 0.0)
            if low == "h":
                x = a[0] + ox
            elif low == "v":
                y = a[0] + oy
            elif low == "a":
                ex, ey = a[5] + ox, a[6] + oy
                pts.extend(arc_points(x, y, a[0], a[1], a[2], a[3], a[4], ex, ey))
                x, y = ex, ey
            else:
                for j in range(0, n, 2):
                    pts.append((a[j] + ox, a[j + 1] + oy))
                x, y = a[-2] + ox, a[-1] + oy
            pts.append((x, y))
            if low == "m" and i == 0:
                sx, sy = x, y
        nums = []

    for letter, number in TOKEN.findall(d):
        if letter:
            flush()
            cmd = letter
        else:
            nums.append(float(number))
    flush()
    return pts


def f(el, name, default=0.0) -> float:
    raw = el.get(name)
    if raw is None:
        return default
    if not NUM.fullmatch(raw.strip()):
        raise ValueError(f"{name}='{raw}' must be a plain number (mm)")
    return float(raw)


def bbox(el):
    tag = local(el.tag)
    if tag in ("rect", "image"):
        x, y, w, h = f(el, "x"), f(el, "y"), f(el, "width"), f(el, "height")
        pts = [(x, y), (x + w, y + h)]
    elif tag == "circle":
        cx, cy, r = f(el, "cx"), f(el, "cy"), f(el, "r")
        pts = [(cx - r, cy - r), (cx + r, cy + r)]
    elif tag == "ellipse":
        cx, cy, rx, ry = f(el, "cx"), f(el, "cy"), f(el, "rx"), f(el, "ry")
        pts = [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    elif tag == "line":
        pts = [(f(el, "x1"), f(el, "y1")), (f(el, "x2"), f(el, "y2"))]
    elif tag in ("polyline", "polygon"):
        v = [float(n) for n in NUM.findall(el.get("points", ""))]
        pts = list(zip(v[0::2], v[1::2]))
    else:
        pts = path_points(el.get("d", ""))
    if not pts:
        raise ValueError("empty geometry")
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def geometry_key(el):
    tag = local(el.tag)
    if tag == "line":
        a, b = (f(el, "x1"), f(el, "y1")), (f(el, "x2"), f(el, "y2"))
        return ("line",) + tuple(sorted((a, b)))
    if tag == "path":
        return ("path", " ".join(TOKEN.sub(lambda m: f" {m.group(0)} ", el.get("d", "")).split()))
    names = ("x", "y", "width", "height", "rx", "ry", "cx", "cy", "r", "points")
    return (tag,) + tuple(" ".join((el.get(n) or "").split()) for n in names)


# ---- main check -------------------------------------------------------------
def check(path, module: str = "laser"):
    """Return (errors, warnings, summary)."""
    errors, warnings = [], []
    summary = {"cut": 0, "score": 0, "print": 0}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"not valid XML: {exc}"], warnings, summary
    if local(root.tag) != "svg":
        return ["root element is not <svg>"], warnings, summary

    bed_w, bed_h = MACHINES["m2"][f"{module}_mm"]
    print_w, print_h = MACHINES["m2"]["print_mm"]

    size = {}
    for dim in ("width", "height"):
        m = re.fullmatch(r"\s*(" + NUM.pattern + r")mm\s*", root.get(dim) or "")
        if not m:
            errors.append(f"<svg {dim}> must be given in mm, e.g. {dim}=\"100mm\"")
        else:
            size[dim] = float(m.group(1))
    vb = [float(n) for n in NUM.findall(root.get("viewBox") or "")]
    if len(vb) != 4:
        errors.append("<svg> needs viewBox=\"0 0 W H\"")
    elif len(size) == 2:
        if abs(vb[0]) > EPS or abs(vb[1]) > EPS:
            errors.append("viewBox must start at 0 0")
        if abs(vb[2] - size["width"]) > 1e-3 or abs(vb[3] - size["height"]) > 1e-3:
            errors.append("viewBox size must equal width/height so 1 unit = 1 mm")
        if size["width"] > bed_w + EPS or size["height"] > bed_h + EPS:
            errors.append(f"document {size['width']}x{size['height']} mm exceeds the {module} bed {bed_w}x{bed_h} mm")
    if errors:
        return errors, warnings, summary
    doc_w, doc_h = size["width"], size["height"]

    seen = {}
    print_box = None

    def walk(el, paint, where):
        nonlocal print_box
        tag = local(el.tag)
        label = f"<{tag}{' id=' + el.get('id') if el.get('id') else ''}> in {where}"
        if tag in BANNED:
            errors.append(f"{label}: not allowed, {BANNED[tag]}")
            return
        if el.get("transform"):
            errors.append(f"{label}: transform not allowed, write final coordinates")
        paint = {**paint, **own_paint(el)}
        if tag in SHAPES:
            stroke, fill = colour(paint.get("stroke")), colour(paint.get("fill", "black"))
            try:
                box = bbox(el)
            except ValueError as exc:
                errors.append(f"{label}: {exc}")
                return
            if box[0] < -EPS or box[1] < -EPS or box[2] > doc_w + EPS or box[3] > doc_h + EPS:
                errors.append(f"{label}: extends outside the document ({', '.join('%.2f' % v for v in box)})")
            role = "cut" if stroke == CUT else "score" if stroke == SCORE else "print"
            if tag == "image":
                role = "print"
            if role in ("cut", "score"):
                if fill is not None:
                    errors.append(f"{label}: {role} line must have fill=\"none\"")
                key = (role,) + geometry_key(el)
                if key in seen:
                    errors.append(f"{label}: duplicate of {seen[key]}, the laser would pass twice")
                seen[key] = label
            else:
                if fill in (CUT, SCORE):
                    warnings.append(f"{label}: fill uses a reserved line colour ({fill})")
                if fill is None and stroke is None and tag != "image":
                    warnings.append(f"{label}: no stroke and no fill, it will be invisible")
                print_box = box if print_box is None else (
                    min(print_box[0], box[0]), min(print_box[1], box[1]),
                    max(print_box[2], box[2]), max(print_box[3], box[3]))
            summary[role] += 1
        for child in el:
            walk(child, paint, el.get("id") or where)

    for child in root:
        walk(child, {}, "svg")

    if print_box:
        pw, ph = print_box[2] - print_box[0], print_box[3] - print_box[1]
        if pw > print_w + EPS or ph > print_h + EPS:
            warnings.append(
                f"print/engrave artwork spans {pw:.1f}x{ph:.1f} mm; the inkjet area is about "
                f"{print_w}x{print_h} mm (fine if this layer is laser-engraved instead)")
    if not any(summary.values()):
        errors.append("no shapes found")
    return errors, warnings, summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("svg", nargs="+")
    ap.add_argument("--module", choices=["laser", "ir"], default="laser")
    args = ap.parse_args(argv)
    failed = False
    for path in args.svg:
        errors, warnings, summary = check(path, args.module)
        print(f"{path}: cut={summary['cut']} score={summary['score']} print/engrave={summary['print']}")
        for w in warnings:
            print(f"  warning: {w}")
        for e in errors:
            print(f"  ERROR: {e}")
        failed |= bool(errors)
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
