"""Tiny SVG writer for xTool M2 jobs. 1 user unit = 1 mm, no transforms.

    from svgjob import Job
    job = Job(width=100, height=60)
    job.cut_rect(0, 0, 100, 60, r=4)
    job.score_line(10, 30, 90, 30)
    job.print_rect(10, 10, 20, 20, fill="#22aa66")
    job.save("build/tag.svg")

Colours are a convention only: xTool Studio groups objects into layers by
colour, and the processing type of each layer is still chosen by hand.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parent.parent
MACHINES = json.loads((ROOT / "machines.json").read_text(encoding="utf-8"))
CUT = MACHINES["svg_roles"]["cut"]
SCORE = MACHINES["svg_roles"]["score"]
HAIRLINE = 0.1


def _n(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


class Job:
    def __init__(self, width: float, height: float):
        self.width, self.height = width, height
        self._layers: dict[str, list[str]] = {"print": [], "score": [], "cut": []}

    # -- low level ---------------------------------------------------------
    def _add(self, layer: str, tag: str, **attrs) -> None:
        body = " ".join(
            f"{k.replace('_', '-')}={quoteattr(_n(v) if isinstance(v, (int, float)) else str(v))}"
            for k, v in attrs.items()
        )
        self._layers[layer].append(f"<{tag} {body}/>")

    def _line_style(self, colour: str) -> dict:
        return {"fill": "none", "stroke": colour, "stroke_width": HAIRLINE}

    def _vector(self, layer: str, colour: str, tag: str, **geom) -> None:
        self._add(layer, tag, **geom, **self._line_style(colour))

    # -- cut (red) ---------------------------------------------------------
    def cut_rect(self, x, y, w, h, r=0.0):
        geom = {"x": x, "y": y, "width": w, "height": h}
        if r:
            geom.update(rx=r, ry=r)
        self._vector("cut", CUT, "rect", **geom)

    def cut_circle(self, cx, cy, r):
        self._vector("cut", CUT, "circle", cx=cx, cy=cy, r=r)

    def cut_path(self, d: str):
        self._vector("cut", CUT, "path", d=d)

    # -- score (blue) ------------------------------------------------------
    def score_line(self, x1, y1, x2, y2):
        self._vector("score", SCORE, "line", x1=x1, y1=y1, x2=x2, y2=y2)

    def score_circle(self, cx, cy, r):
        self._vector("score", SCORE, "circle", cx=cx, cy=cy, r=r)

    def score_path(self, d: str):
        self._vector("score", SCORE, "path", d=d)

    # -- print / engrave (filled, any colour except pure red or blue) ------
    def print_rect(self, x, y, w, h, fill="#000000"):
        self._add("print", "rect", x=x, y=y, width=w, height=h, fill=fill, stroke="none")

    def print_circle(self, cx, cy, r, fill="#000000"):
        self._add("print", "circle", cx=cx, cy=cy, r=r, fill=fill, stroke="none")

    def print_path(self, d: str, fill="#000000"):
        self._add("print", "path", d=d, fill=fill, stroke="none")

    # -- output ------------------------------------------------------------
    def to_svg(self) -> str:
        w, h = _n(self.width), _n(self.height)
        out = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
        ]
        # print first, cut last: the order the machine should work in
        for layer in ("print", "score", "cut"):
            if self._layers[layer]:
                out.append(f'  <g id="{layer}">')
                out += [f"    {el}" for el in self._layers[layer]]
                out.append("  </g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def save(self, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_svg(), encoding="utf-8")
        return path
