"""Template population: fit each personalization slot into its box using real font
metrics, swap in the brand palette, and grow the per-order procedural art."""
from __future__ import annotations

import hashlib
import json
import math
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .fonts import metrics
from .schema import THEMES, Order, event_line, format_date, format_time, names_text

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


@dataclass
class SlotSpec:
    name: str
    box: tuple[float, float, float, float]
    font: str
    weight: str
    style: str
    min_size: float
    max_size: float
    max_lines: int
    align: str
    color: str
    transform: str
    tracking: float
    voice: str
    lh: float

    @classmethod
    def from_el(cls, el: ET.Element) -> "SlotSpec":
        a = el.attrib
        return cls(
            name=a["data-slot"], box=tuple(float(v) for v in a["data-box"].split()),
            font=a["data-font"], weight=a["data-weight"], style=a["data-style"],
            min_size=float(a["data-min"]), max_size=float(a["data-max"]),
            max_lines=int(a["data-lines"]), align=a["data-align"], color=a["data-color"],
            transform=a["data-transform"], tracking=float(a["data-tracking"]),
            voice=a["data-voice"], lh=float(a["data-lh"]),
        )


@lru_cache(maxsize=None)
def _template_source(name: str) -> str:
    return (TEMPLATE_DIR / f"{name}.svg").read_text()


def audit_library() -> dict:
    """Structure the SVG library into a machine-readable schema: slots, boxes, fonts, palettes."""
    out = {}
    for path in sorted(TEMPLATE_DIR.glob("*.svg")):
        root = ET.fromstring(path.read_text())
        out[path.stem] = {
            "fonts": root.attrib["data-fonts"].split(","),
            "palettes": json.loads(root.attrib["data-palettes"]),
            "slots": [SlotSpec.from_el(el).__dict__ for el in root.iter(f"{{{SVG_NS}}}text") if "data-slot" in el.attrib],
            "procedural": [el.attrib["data-procedural"] for el in root.iter() if "data-procedural" in el.attrib],
        }
    return out


def slot_texts(order: Order) -> dict[str, str]:
    return {
        "headline": order.headline or "",
        "names": names_text(order.names),
        "event_line": event_line(order),
        "date": order.date,
        "time": order.time or "",
        "venue": order.venue or "",
        "city": order.city or "",
        "rsvp": order.rsvp or "",
    }


def _display(spec: SlotSpec, raw: str) -> str:
    if spec.name == "date":
        raw = format_date(raw, spec.voice)
    elif spec.name == "time":
        raw = format_time(raw, spec.voice)
    return raw.upper() if spec.transform == "upper" else raw


def wrap(words: list[str], width: float, measure) -> list[str]:
    lines, cur = [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if cur and measure(cand) > width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def balance(words: list[str], n: int, width: float, measure) -> list[str]:
    """Narrowest wrap that still uses n lines, so lines come out even (no orphan words)."""
    lo, hi = 0.0, width
    best = wrap(words, width, measure)
    for _ in range(18):
        mid = (lo + hi) / 2
        cand = wrap(words, mid, measure)
        if len(cand) <= n and all(measure(l) <= width for l in cand):
            best, hi = cand, mid
        else:
            lo = mid
    # Keep "&" with the name that follows it.
    for i in range(len(best) - 1):
        if best[i].endswith(" &"):
            best[i], best[i + 1] = best[i][:-2], "& " + best[i + 1]
    return best


def fit(spec: SlotSpec, text: str) -> dict:
    """Largest font size in the slot's range whose wrapped lines fit the box."""
    m = metrics(spec.font, spec.weight, spec.style)
    x, y, w, h = spec.box
    words = text.split()
    size = spec.max_size
    while True:
        meas = lambda s, z=size: m.width(s, z, spec.tracking)
        lines = wrap(words, w, meas)
        widest = max((meas(l) for l in lines), default=0)
        height = len(lines) * size * spec.lh
        ok = len(lines) <= spec.max_lines and widest <= w and height <= h
        if ok or size <= spec.min_size:
            if ok and len(lines) > 1:
                lines = balance(words, len(lines), w, meas)
            return {"lines": lines, "size": round(size, 2), "fits": ok, "widest": round(widest, 1),
                    "height": round(height, 1), "ascent": m.ascent, "descent": m.descent,
                    "glyphs_ok": m.covers(text)}
        size = max(spec.min_size, size - 0.5)


def _seed(order: Order) -> int:
    return int(hashlib.sha256(names_text(order.names).encode()).hexdigest()[:8], 16)


def _flourish(box, color) -> list[ET.Element]:
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    half = w / 2
    d = (f"M{cx - 6},{cy} C{cx - half * .35},{cy - h * .55} {cx - half * .7},{cy + h * .5} {cx - half},{cy} "
         f"M{cx + 6},{cy} C{cx + half * .35},{cy - h * .55} {cx + half * .7},{cy + h * .5} {cx + half},{cy}")
    path = ET.Element(f"{{{SVG_NS}}}path", {"d": d, "fill": "none", "stroke": color, "stroke-width": "1.1",
                                            "stroke-linecap": "round"})
    dia = ET.Element(f"{{{SVG_NS}}}path", {"d": f"M{cx},{cy - 4} L{cx + 4},{cy} L{cx},{cy + 4} L{cx - 4},{cy} Z",
                                           "fill": color})
    return [path, dia]


def _leaf(x, y, length, angle, color) -> ET.Element:
    w = length * 0.38
    d = f"M0,0 Q{length / 2},{-w} {length},0 Q{length / 2},{w} 0,0 Z"
    return ET.Element(f"{{{SVG_NS}}}path", {"d": d, "fill": color, "opacity": "0.9",
                                            "transform": f"translate({x:.1f},{y:.1f}) rotate({angle:.1f})"})


def _leaves(box, edge, pal, rng) -> list[ET.Element]:
    """Branches curving in from the corners, with leaves placed along each stem."""
    x, y, w, h = box
    els = []
    for side in (-1, 1):
        for b in range(rng.randint(2, 3)):
            ox = x + (0 if side < 0 else w)
            oy = y + (rng.uniform(0, h * .4) if edge == "top" else h - rng.uniform(0, h * .4))
            span = rng.uniform(w * .22, w * .42)
            dy = rng.uniform(h * .25, h * .7) * (1 if edge == "top" else -1)
            ex, ey = ox - side * span, oy + dy
            c1x, c1y = ox - side * span * .4, oy + dy * .05
            stem = ET.Element(f"{{{SVG_NS}}}path", {
                "d": f"M{ox:.1f},{oy:.1f} Q{c1x:.1f},{c1y:.1f} {ex:.1f},{ey:.1f}",
                "fill": "none", "stroke": pal["accent"], "stroke-width": "1.4", "stroke-linecap": "round"})
            els.append(stem)
            n = rng.randint(4, 7)
            for i in range(1, n + 1):
                t = i / (n + 1)
                px = (1 - t) ** 2 * ox + 2 * (1 - t) * t * c1x + t * t * ex
                py = (1 - t) ** 2 * oy + 2 * (1 - t) * t * c1y + t * t * ey
                tx = 2 * (1 - t) * (c1x - ox) + 2 * t * (ex - c1x)
                ty = 2 * (1 - t) * (c1y - oy) + 2 * t * (ey - c1y)
                base = math.degrees(math.atan2(ty, tx))
                for s in (-1, 1):
                    if rng.random() < .85:
                        color = pal["accent"] if rng.random() < .5 else pal.get("accent2", pal["accent"])
                        els.append(_leaf(px, py, rng.uniform(16, 28) * (1 - t * .4), base + s * rng.uniform(35, 60), color))
    return els


def _confetti(box, pal, rng) -> list[ET.Element]:
    x, y, w, h = box
    colors = [pal[k] for k in ("accent", "accent2", "accent3") if k in pal]
    els = []
    for _ in range(46):
        cx, cy = rng.uniform(x + 8, x + w - 8), rng.uniform(y + 8, y + h - 8)
        c, kind, rot = rng.choice(colors), rng.random(), rng.uniform(0, 180)
        if kind < .35:
            els.append(ET.Element(f"{{{SVG_NS}}}circle", {"cx": f"{cx:.1f}", "cy": f"{cy:.1f}", "r": f"{rng.uniform(2.5, 5.5):.1f}", "fill": c}))
        elif kind < .7:
            els.append(ET.Element(f"{{{SVG_NS}}}rect", {"x": "-6", "y": "-2.5", "width": "12", "height": "5", "rx": "1", "fill": c,
                                                        "transform": f"translate({cx:.1f},{cy:.1f}) rotate({rot:.0f})"}))
        else:
            els.append(ET.Element(f"{{{SVG_NS}}}path", {"d": "M-8,0 q4,-6 8,0 t8,0", "fill": "none", "stroke": c, "stroke-width": "2.2",
                                                        "stroke-linecap": "round", "transform": f"translate({cx:.1f},{cy:.1f}) rotate({rot:.0f})"}))
    return els


def render(order: Order, theme: str | None = None) -> tuple[str, dict]:
    theme = theme or order.theme_or_default
    template, palette_name = THEMES[theme]
    root = ET.fromstring(_template_source(template))
    pal = json.loads(root.attrib["data-palettes"])[palette_name]
    rng = random.Random(_seed(order))
    texts = slot_texts(order)
    report = {"theme": theme, "template": template, "palette": palette_name, "slots": {}}

    for el in list(root.iter()):
        role = el.attrib.get("data-color")
        if role and el.tag != f"{{{SVG_NS}}}text" and "data-procedural" not in el.attrib:
            el.set("stroke" if el.attrib.get("data-paint") == "stroke" else "fill", pal[role])

    for parent in list(root.iter()):
        for i, el in enumerate(list(parent)):
            kind = el.attrib.get("data-procedural")
            if kind:
                box = tuple(float(v) for v in el.attrib["data-box"].split())
                g = ET.Element(f"{{{SVG_NS}}}g", {"data-procedural": kind})
                if kind == "flourish":
                    kids = _flourish(box, pal[el.attrib.get("data-color", "accent")])
                elif kind == "leaves":
                    kids = _leaves(box, el.attrib.get("data-edge", "top"), pal, rng)
                else:
                    kids = _confetti(box, pal, rng)
                g.extend(kids)
                parent.remove(el)
                parent.insert(i, g)

    for el in list(root.iter(f"{{{SVG_NS}}}text")):
        if "data-slot" not in el.attrib:
            continue
        spec = SlotSpec.from_el(el)
        text = _display(spec, texts.get(spec.name, ""))
        for k in list(el.attrib):
            if k.startswith("data-") and k != "data-slot":
                del el.attrib[k]
        if not text:
            report["slots"][spec.name] = {"text": "", "empty": True, "fits": True}
            continue
        r = fit(spec, text)
        x, y, w, h = spec.box
        n = len(r["lines"])
        lh = r["size"] * spec.lh
        top = y + (h - n * lh) / 2 + (lh - r["size"] * (r["ascent"] + r["descent"])) / 2 + r["size"] * r["ascent"]
        ax = x + w / 2 if spec.align == "middle" else x
        el.attrib.update({
            "x": f"{ax:.1f}", "y": f"{top:.1f}", "font-family": spec.font, "font-size": f"{r['size']}",
            "font-weight": spec.weight, "font-style": spec.style, "fill": pal[spec.color],
            "text-anchor": spec.align,
        })
        if spec.tracking:
            el.set("letter-spacing", f"{spec.tracking}")
        for j, line in enumerate(r["lines"]):
            ts = ET.SubElement(el, f"{{{SVG_NS}}}tspan", {"x": f"{ax:.1f}", "dy": "0" if j == 0 else f"{lh:.2f}"})
            ts.text = line
        report["slots"][spec.name] = {"text": text, "size": r["size"], "lines": n, "fits": r["fits"],
                                      "glyphs_ok": r["glyphs_ok"], "box": spec.box, "font": spec.font}

    for k in ("data-palettes", "data-fonts"):
        root.attrib.pop(k, None)
    root.set("data-theme", theme)
    return ET.tostring(root, encoding="unicode"), report
