"""Deterministic checks every output must pass before it can ship without a human."""
from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ET

from .layout import TEMPLATE_DIR, SVG_NS
from .schema import EVENT_TYPES, THEMES, Order, parse_date


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def run_checks(order: Order, svg: str, report: dict, source_text: str | None = None,
               order_date: str | None = None) -> list[dict]:
    out = []

    def add(name, ok, detail=""):
        out.append({"check": name, "ok": bool(ok), "detail": detail})

    # 1. The SVG parses and is an SVG document.
    try:
        root = ET.fromstring(svg)
        add("valid_svg", root.tag == f"{{{SVG_NS}}}svg")
    except ET.ParseError as e:
        add("valid_svg", False, str(e))
        return out

    # 2. Required fields.
    add("event_type_known", order.event_type in EVENT_TYPES, order.event_type)
    add("has_names", bool(order.names), ", ".join(order.names))
    d = parse_date(order.date)
    add("date_valid", d is not None, order.date)
    if d and order_date:
        od = parse_date(order_date)
        add("date_in_future", od is None or d >= od, f"event {order.date}, ordered {order_date}")
    if order.event_type == "birthday" and order.age is not None:
        add("age_plausible", 0 < order.age < 120, str(order.age))

    # 3. Personalization accuracy: every name appears verbatim in the rendered text.
    rendered = " ".join("".join(t.itertext()) for t in root.iter(f"{{{SVG_NS}}}text"))
    missing = [n for n in order.names if n.upper() not in rendered.upper()]
    add("names_rendered_exactly", not missing, "missing: " + ", ".join(missing) if missing else "")

    # 4. Grounding: names and venue must come from the customer's own words (catches hallucinations).
    if source_text is not None:
        src = _norm(source_text)
        ungrounded = [n for n in order.names if _norm(n) and _norm(n) not in src]
        add("names_grounded_in_order", not ungrounded, ", ".join(ungrounded))
        if order.venue:
            add("venue_grounded_in_order", _norm(order.venue) in src, order.venue)

    # 5. Layout: nothing overflows its box, every glyph exists in the font.
    over = [k for k, v in report["slots"].items() if not v.get("fits", True)]
    add("no_text_overflow", not over, ", ".join(over))
    bad_glyphs = [k for k, v in report["slots"].items() if v.get("glyphs_ok") is False]
    add("glyphs_supported", not bad_glyphs, ", ".join(bad_glyphs))

    # 6. Brand consistency: only the template's palette colors and approved fonts.
    tpl = ET.fromstring((TEMPLATE_DIR / f"{report['template']}.svg").read_text())
    allowed_colors = {c.upper() for c in json.loads(tpl.attrib["data-palettes"])[report["palette"]].values()}
    used_colors = {v.upper() for el in root.iter() for k, v in el.attrib.items()
                   if k in ("fill", "stroke") and v.startswith("#")}
    off_brand = used_colors - allowed_colors
    add("palette_on_brand", not off_brand, ", ".join(sorted(off_brand)))
    allowed_fonts = set(tpl.attrib["data-fonts"].split(","))
    used_fonts = {el.attrib["font-family"] for el in root.iter() if "font-family" in el.attrib}
    add("fonts_on_brand", used_fonts <= allowed_fonts, ", ".join(sorted(used_fonts - allowed_fonts)))
    add("theme_allowed", report["theme"] in THEMES, report["theme"])
    return out
