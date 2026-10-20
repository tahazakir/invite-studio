"""Hand-written regex parser: the no-ML baseline a team would build first."""
from __future__ import annotations

import datetime as dt
import re

from .datagen import CITIES, EVENT_WORDS, THEME_HINTS
from .schema import DEFAULT_THEME

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September",
     "October", "November", "December"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"


def _next(month, day, year, od):
    if year:
        return dt.date(int(year), month, day)
    d = dt.date(od.year, month, day)
    return d if d >= od else dt.date(od.year + 1, month, day)


def parse_date(t: str, od: dt.date) -> str | None:
    s = t.lower()
    try:
        if m := re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", s):
            return dt.date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        if m := re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s):
            return dt.date(int(m[3]), int(m[2]), int(m[1])).isoformat()
        if m := re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?(?: of)?[ -]{MON}\b,?[ -]?(\d{{4}})?", s):
            return _next(MONTHS[m[2][:3]], int(m[1]), m[3], od).isoformat()
        if m := re.search(rf"\b{MON} (\d{{1,2}})(?:st|nd|rd|th)?\b,? ?(\d{{4}})?", s):
            return _next(MONTHS[m[1][:3]], int(m[2]), m[3], od).isoformat()
    except ValueError:
        return None
    return None


def parse_time(t: str) -> str | None:
    s = t.lower()
    if m := re.search(r"\b(\d{1,2})[:.](\d{2})\s*(am|pm)\b", s):
        h = int(m[1]) % 12 + (12 if m[3] == "pm" else 0)
        return f"{h:02d}:{m[2]}"
    if m := re.search(r"\b(\d{1,2})\s*(am|pm)\b", s):
        return f"{int(m[1]) % 12 + (12 if m[2] == 'pm' else 0):02d}:00"
    if m := re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", s):
        return f"{int(m[1]):02d}:{m[2]}"
    return None


def parse(text: str, order_date: str) -> dict:
    od = dt.date.fromisoformat(order_date)
    low = text.lower()
    event = next((e for e, words in sorted(EVENT_WORDS.items()) for w in sorted(words, key=len, reverse=True)
                  if w in low), "wedding")
    names = []
    NAME = r"([^\W\d][\w'\-]*(?: (?!and\b)[^\W\d][\w'\-]*)?)"
    if m := re.search(rf"(?:names?:|who=|\bof|\bfor|celebrating|^)\s*{NAME}\s*(?:&|\band\b|\+)\s*{NAME}", text, re.I | re.M):
        names = [m[1], m[2]]
    elif m := re.search(rf"(?:names?:|who=|\bof|\bfor|celebrating)\s+{NAME}", text, re.I):
        names = [m[1]]
    names = [n if not n.islower() else n.title() for n in names]
    theme = DEFAULT_THEME[event]
    for th, hints in THEME_HINTS.items():
        if any(h in low for h in hints):
            theme = th
    venue = None
    if m := re.search(r"(?:venue(?: is)?:?|place=|where:|at)\s+([A-Z][^,.;\n/]+)", text):
        venue = m[1].strip()
    headline = None
    if m := re.search(r"[\"']([^\"']{3,40})[\"']", text):
        headline = m[1]
    age = None
    if m := re.search(r"\b(?:turning|age:?|age=|be)\s*(\d{1,3})\b|\b(\d{1,3})(?:st|nd|rd|th) birthday", low):
        age = int(m[1] or m[2])
    rsvp = None
    if m := re.search(r"((?:RSVP|Regrets only|Kindly reply)[^\n.;/]*(?:\.\d[^\n;/]*)?)", text):
        rsvp = m[1].strip()
    city = next((c for c in sorted(CITIES, key=len, reverse=True) if c.lower() in low), None)
    if venue and city and venue.endswith(city):
        venue = venue[: -len(city)].rstrip(", ")
    return {"event_type": event, "names": names, "date": parse_date(text, od), "time": parse_time(text),
            "venue": venue, "city": city, "headline": headline, "age": age, "rsvp": rsvp, "theme": theme}
