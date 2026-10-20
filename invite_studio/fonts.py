"""Real font metrics from the macOS system fonts, so text is measured, not guessed."""
from __future__ import annotations

from functools import lru_cache

from fontTools.ttLib import TTCollection, TTFont

SUP = "/System/Library/Fonts/Supplemental/"

# (css family, css weight, css style) -> (file, index in collection)
FONT_FILES = {
    ("Didot", "normal", "normal"): ("Didot.ttc", 0),
    ("Didot", "normal", "italic"): ("Didot.ttc", 1),
    ("Didot", "bold", "normal"): ("Didot.ttc", 2),
    ("Snell Roundhand", "normal", "normal"): ("SnellRoundhand.ttc", 0),
    ("Snell Roundhand", "bold", "normal"): ("SnellRoundhand.ttc", 1),
    ("Baskerville", "normal", "normal"): ("Baskerville.ttc", 0),
    ("Baskerville", "normal", "italic"): ("Baskerville.ttc", 2),
    ("Baskerville", "600", "normal"): ("Baskerville.ttc", 4),
    ("Savoye LET", "normal", "normal"): ("Savoye LET.ttc", 0),
    ("Futura", "normal", "normal"): ("Futura.ttc", 0),
    ("Futura", "bold", "normal"): ("Futura.ttc", 2),
    ("Copperplate", "normal", "normal"): ("Copperplate.ttc", 0),
    ("Copperplate", "bold", "normal"): ("Copperplate.ttc", 2),
}


class Metrics:
    def __init__(self, font: TTFont):
        self.upem = font["head"].unitsPerEm
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"].metrics
        self.ascent = font["hhea"].ascent / self.upem
        self.descent = -font["hhea"].descent / self.upem
        self.missing = self.hmtx.get(".notdef", (self.upem // 2, 0))[0]

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        units = 0
        for ch in text:
            g = self.cmap.get(ord(ch))
            units += self.hmtx[g][0] if g in self.hmtx else self.missing
        return units / self.upem * size + tracking * max(len(text) - 1, 0)

    def covers(self, text: str) -> bool:
        return all(ord(ch) in self.cmap or ch.isspace() for ch in text)


@lru_cache(maxsize=None)
def metrics(family: str, weight: str = "normal", style: str = "normal") -> Metrics:
    path, idx = FONT_FILES[(family, weight, style)]
    path = SUP + path
    font = TTCollection(path).fonts[idx] if path.endswith(".ttc") else TTFont(path)
    return Metrics(font)
