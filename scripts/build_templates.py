"""Writes the template library to templates/*.svg.

Each template is a plain SVG file. Personalization slots are <text> elements with
data-* attributes (box, font, size range, max lines, alignment, color role); the
root element carries the brand rules (allowed palettes). Decorative art that varies
per order is a <g data-procedural=...> placeholder. A real library would be authored
in a design tool and annotated the same way.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "templates"

PALETTES = {
    "classic": {
        "gold": {"paper": "#FBF7F0", "ink": "#3B3226", "accent": "#B08D57"},
        "blush": {"paper": "#FFF6F4", "ink": "#4A2E2E", "accent": "#C98B8B"},
    },
    "botanical": {
        "sage": {"paper": "#F5F7F2", "ink": "#2F3B2F", "accent": "#7D9B76", "accent2": "#A9BFA3"},
        "terracotta": {"paper": "#FBF4EE", "ink": "#40302A", "accent": "#C07A5A", "accent2": "#D9A98E"},
    },
    "modern": {
        "navy": {"paper": "#FFFFFF", "ink": "#1B2440", "accent": "#E4B363"},
        "mono": {"paper": "#FAFAF7", "ink": "#111111", "accent": "#9A9A9A"},
    },
    "party": {
        "candy": {"paper": "#FFF9F0", "ink": "#2B2B5A", "accent": "#FF6B6B", "accent2": "#4ECDC4", "accent3": "#FFD93D"},
        "ocean": {"paper": "#F2FAFC", "ink": "#0B3C5D", "accent": "#328CC1", "accent2": "#1DD3B0", "accent3": "#F2C14E"},
    },
}


def slot(name, box, font, size, lines, color="ink", align="middle", weight="normal",
         style="normal", transform="none", tracking=0, voice="standard", lh=1.2):
    x, y, w, h = box
    return (f'<text data-slot="{name}" data-box="{x} {y} {w} {h}" data-font="{font}" '
            f'data-weight="{weight}" data-style="{style}" data-min="{size[0]}" data-max="{size[1]}" '
            f'data-lines="{lines}" data-align="{align}" data-color="{color}" '
            f'data-transform="{transform}" data-tracking="{tracking}" data-voice="{voice}" '
            f'data-lh="{lh}"/>')


def svg(name, body, fonts):
    pal = json.dumps(PALETTES[name]).replace('"', "&quot;")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" width="500" height="700" '
            f'data-template="{name}" data-palettes="{pal}" data-fonts="{",".join(fonts)}">\n'
            f'<rect data-color="paper" x="0" y="0" width="500" height="700"/>\n'
            + "\n".join(body) + "\n</svg>\n")


classic = svg("classic", [
    '<rect data-color="accent" data-paint="stroke" x="24" y="24" width="452" height="652" fill="none" stroke-width="1.5"/>',
    '<rect data-color="accent" data-paint="stroke" x="34" y="34" width="432" height="632" fill="none" stroke-width="0.6"/>',
    '<g data-procedural="flourish" data-box="150 70 200 30" data-color="accent"/>',
    slot("headline", (70, 110, 360, 50), "Didot", (13, 19), 2, style="italic"),
    slot("names", (64, 165, 372, 150), "Snell Roundhand", (30, 62), 3, lh=1.05),
    slot("event_line", (70, 320, 360, 64), "Didot", (12, 16), 3, style="italic"),
    '<g data-procedural="flourish" data-box="190 392 120 18" data-color="accent"/>',
    slot("date", (60, 416, 380, 48), "Didot", (13, 18), 2, voice="formal"),
    slot("time", (60, 466, 380, 28), "Didot", (12, 16), 1, style="italic", voice="formal"),
    slot("venue", (60, 504, 380, 56), "Didot", (13, 18), 2, transform="upper", tracking=1.5),
    slot("city", (60, 562, 380, 26), "Didot", (11, 14), 1, color="accent", transform="upper", tracking=3),
    slot("rsvp", (80, 610, 340, 40), "Didot", (10, 12), 2, style="italic"),
], ["Didot", "Snell Roundhand"])

botanical = svg("botanical", [
    '<g data-procedural="leaves" data-box="0 0 500 140" data-edge="top"/>',
    '<g data-procedural="leaves" data-box="0 600 500 100" data-edge="bottom"/>',
    slot("headline", (70, 150, 360, 40), "Baskerville", (13, 18), 2, style="italic"),
    slot("names", (40, 192, 420, 156), "Savoye LET", (38, 76), 3, lh=1.0),
    slot("event_line", (70, 350, 360, 58), "Baskerville", (12, 16), 3, style="italic"),
    slot("date", (60, 414, 380, 42), "Baskerville", (12, 16), 2, weight="600", transform="upper", tracking=1.5),
    slot("time", (60, 456, 380, 26), "Baskerville", (12, 15), 1),
    slot("venue", (60, 486, 380, 46), "Baskerville", (13, 17), 2),
    slot("city", (60, 532, 380, 24), "Baskerville", (11, 14), 1, color="accent", style="italic"),
    slot("rsvp", (80, 560, 340, 34), "Baskerville", (10, 12), 2, style="italic"),
], ["Baskerville", "Savoye LET"])

modern = svg("modern", [
    '<rect data-color="ink" x="0" y="0" width="500" height="262"/>',
    slot("headline", (50, 48, 400, 40), "Futura", (11, 14), 2, color="accent", align="start", transform="upper", tracking=3),
    slot("names", (50, 92, 400, 150), "Futura", (28, 56), 3, color="paper", align="start", weight="bold", transform="upper", lh=1.05),
    '<rect data-color="accent" x="50" y="292" width="60" height="4"/>',
    slot("event_line", (50, 312, 400, 62), "Futura", (13, 17), 3, align="start"),
    slot("date", (50, 400, 400, 36), "Futura", (18, 26), 1, align="start", weight="bold", voice="modern"),
    slot("time", (50, 440, 400, 28), "Futura", (14, 18), 1, align="start"),
    slot("venue", (50, 488, 400, 52), "Futura", (14, 18), 2, align="start", weight="bold"),
    slot("city", (50, 540, 400, 26), "Futura", (11, 14), 1, color="accent", align="start", transform="upper", tracking=2),
    slot("rsvp", (50, 620, 400, 40), "Futura", (10, 12), 2, align="start"),
], ["Futura"])

party = svg("party", [
    '<g data-procedural="confetti" data-box="0 0 500 140"/>',
    '<g data-procedural="confetti" data-box="0 600 500 100"/>',
    slot("headline", (50, 148, 400, 40), "Copperplate", (14, 20), 2, color="accent", weight="bold", tracking=2),
    slot("names", (40, 192, 420, 144), "Futura", (34, 70), 2, weight="bold", lh=1.05),
    slot("event_line", (60, 340, 380, 58), "Futura", (14, 19), 2),
    slot("date", (60, 410, 380, 34), "Copperplate", (15, 20), 1, weight="bold"),
    slot("time", (60, 446, 380, 26), "Copperplate", (13, 16), 1),
    slot("venue", (60, 480, 380, 46), "Futura", (14, 18), 2, weight="bold"),
    slot("city", (60, 526, 380, 24), "Futura", (11, 14), 1, color="accent"),
    slot("rsvp", (60, 560, 380, 34), "Futura", (10, 12), 2),
], ["Futura", "Copperplate"])

OUT.mkdir(exist_ok=True)
for name, s in [("classic", classic), ("botanical", botanical), ("modern", modern), ("party", party)]:
    (OUT / f"{name}.svg").write_text(s)
    print("wrote", OUT / f"{name}.svg")
