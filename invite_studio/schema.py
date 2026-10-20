"""The structured order schema shared by the parser, the model, and the renderer."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass, field

EVENT_TYPES = ["wedding", "engagement", "anniversary", "birthday", "baby_shower"]

# Theme = template + brand palette. These are the only combinations the brand allows.
THEMES = {
    "classic-gold": ("classic", "gold"),
    "classic-blush": ("classic", "blush"),
    "botanical-sage": ("botanical", "sage"),
    "botanical-terracotta": ("botanical", "terracotta"),
    "modern-navy": ("modern", "navy"),
    "modern-mono": ("modern", "mono"),
    "party-candy": ("party", "candy"),
    "party-ocean": ("party", "ocean"),
}

DEFAULT_THEME = {
    "wedding": "classic-gold",
    "engagement": "botanical-sage",
    "anniversary": "classic-blush",
    "birthday": "party-candy",
    "baby_shower": "botanical-sage",
}

FIELDS = ["event_type", "names", "headline", "date", "time", "venue", "city", "age", "rsvp", "theme"]


@dataclass
class Order:
    event_type: str
    names: list[str]
    date: str  # ISO yyyy-mm-dd
    time: str | None = None  # HH:MM, 24h
    venue: str | None = None
    city: str | None = None
    headline: str | None = None
    age: int | None = None
    rsvp: str | None = None
    theme: str | None = None
    extras: dict = field(default_factory=dict)

    def to_json(self) -> str:
        d = {k: getattr(self, k) for k in FIELDS}
        return json.dumps(d, ensure_ascii=False)

    @property
    def theme_or_default(self) -> str:
        if self.theme in THEMES:
            return self.theme
        return DEFAULT_THEME.get(self.event_type, "classic-gold")

    @classmethod
    def from_dict(cls, d: dict) -> "Order":
        names = d.get("names") or []
        if isinstance(names, str):
            names = [n.strip() for n in names.replace(" and ", "&").split("&") if n.strip()]
        age = d.get("age")
        try:
            age = int(age) if age not in (None, "") else None
        except (TypeError, ValueError):
            age = None
        return cls(
            event_type=d.get("event_type") or "wedding",
            names=list(names),
            date=d.get("date") or "",
            time=d.get("time") or None,
            venue=d.get("venue") or None,
            city=d.get("city") or None,
            headline=d.get("headline") or None,
            age=age,
            rsvp=d.get("rsvp") or None,
            theme=d.get("theme") or None,
        )

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("extras")
        return d


# ---------- display formatting (per template voice) ----------

ORDINAL_WORDS = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh",
    8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth",
    14: "fourteenth", 15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
    19: "nineteenth", 20: "twentieth", 21: "twenty-first", 22: "twenty-second",
    23: "twenty-third", 24: "twenty-fourth", 25: "twenty-fifth", 26: "twenty-sixth",
    27: "twenty-seventh", 28: "twenty-eighth", 29: "twenty-ninth", 30: "thirtieth",
    31: "thirty-first",
}
HOUR_WORDS = ["twelve", "one", "two", "three", "four", "five", "six", "seven", "eight",
              "nine", "ten", "eleven"]


def parse_date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def format_date(iso: str, voice: str) -> str:
    d = parse_date(iso)
    if d is None:
        return iso or ""
    if voice == "formal":
        return f"{d:%A}, the {ORDINAL_WORDS[d.day]} of {d:%B}, {d.year}"
    if voice == "modern":
        return f"{d:%a} {d.day:02d}.{d.month:02d}.{d.year}"
    return f"{d:%A}, {d:%B} {d.day}, {d.year}"


def format_time(hhmm: str | None, voice: str) -> str:
    if not hhmm:
        return ""
    try:
        h, m = (int(x) for x in hhmm.split(":"))
    except ValueError:
        return hhmm
    if voice == "formal" and m in (0, 30):
        part = "in the morning" if h < 12 else "in the afternoon" if h < 17 else "in the evening"
        word = HOUR_WORDS[h % 12]
        return f"at {'half past ' + word if m == 30 else word + " o'clock"} {part}"
    suffix = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12}:{m:02d} {suffix}"


def event_line(order: Order) -> str:
    plural = len(order.names) > 1
    t = order.event_type
    if t == "wedding":
        return ("request" if plural else "requests") + " the pleasure of your company at the celebration of their marriage"
    if t == "engagement":
        return ("invite" if plural else "invites") + " you to celebrate their engagement"
    if t == "anniversary":
        return ("invite" if plural else "invites") + " you to celebrate their anniversary"
    if t == "birthday":
        if order.age:
            return f"{'are' if plural else 'is'} turning {order.age}! Join us to celebrate"
        return "Join us for a birthday celebration"
    if t == "baby_shower":
        return "Join us for a baby shower in honor of the parents-to-be" if plural else "Join us for a baby shower in honor of the mother-to-be"
    return ""


def names_text(names: list[str]) -> str:
    return " & ".join(names)
