"""Synthetic free-text invitation orders paired with their correct structured fields.

Orders imitate the personalization box on a print-on-demand listing: inconsistent
date and time formats, missing years, chatter, color hints instead of theme names.
Phrasing styles are split into TRAIN_STYLES and TEST_STYLES so evaluation measures
generalization to wordings the model never saw.
"""
from __future__ import annotations

import datetime as dt
import random

from .schema import DEFAULT_THEME, Order

FIRST = ["Sarah", "Ahmed", "Ayesha", "Omar", "Fatima", "Hamza", "Zainab", "Bilal", "Hina", "Usman",
         "Mariam", "Ali", "Emma", "Liam", "Olivia", "Noah", "Sofia", "Mateo", "Chloe", "Daniel",
         "Priya", "Arjun", "Mei", "Wei", "Amara", "Kwame", "Isabella", "Lucas", "Nour", "Yusuf",
         "Maximilian", "Anastasia", "Bartholomew", "Guinevere", "Zoë", "José", "Renée", "Siobhan",
         "Jo", "Bo", "Eli", "Ava", "Mohammad Taha", "Mary-Kate", "Jean-Luc", "Anne-Marie",
         "Saoirse", "Oluwaseun", "Esperanza", "Thandiwe", "Rania", "Faisal", "Khadija", "Imran"]
LAST = ["Khan", "Siddiqui", "Malik", "Chaudhry", "Qureshi", "Smith", "Garcia", "Nguyen", "Okafor",
        "Rossi", "O'Brien", "McKenzie", "van der Berg", "Fitzgerald-Hughes", "Haider", "Rahman"]
VENUES = ["The Grand Hall", "Pearl Continental", "Royal Palm Golf & Country Club", "Rose Garden Marquee",
          "St. Mary's Church", "The Old Mill Barn", "Funland Trampoline Park", "Our Backyard",
          "Nishat Hotel Ballroom", "The Glasshouse", "Lakeview Pavilion", "Café Mocha",
          "The Boathouse on Lake Como", "Serena Hotel", "Faletti's Hotel", "Community Centre Hall 2",
          "Avari Towers Rooftop", "The Botanical Gardens Conservatory", "Willow Creek Farm",
          "Bounce House Party Zone", "Marriott Crystal Ballroom", "The Lighthouse Inn"]
CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Multan", "Peshawar", "London", "Dubai",
          "Toronto", "New York", "Austin, TX", "Manchester", "Pittsburgh", "Sydney", "Lisbon"]
HEADLINES = {
    "wedding": ["Together with their families", "Save the date", "Bismillah", "Two hearts, one love",
                "With joyful hearts"],
    "engagement": ["She said yes!", "Let's celebrate", "Love is in the air"],
    "anniversary": ["25 years of love", "Golden anniversary", "Still crazy about each other"],
    "birthday": ["You're invited!", "Let's party", "Oh, the fun we'll have", "Party time"],
    "baby_shower": ["Oh baby!", "A little one is on the way", "Twinkle twinkle little star"],
}
RSVP = ["RSVP to {a} by {d}", "Regrets only: {p}", "RSVP {p}", "Kindly reply to {a} by {d}",
        "RSVP to {a} at {p}"]
PHONES = ["0300 1234567", "0321-7654321", "+44 7700 900123", "(412) 555-0199", "0333 9876543"]

# phrase a customer might use -> theme it implies
THEME_HINTS = {
    "classic-gold": ["gold", "classic gold", "elegant gold", "ivory and gold"],
    "classic-blush": ["blush", "blush pink", "soft pink", "dusty rose"],
    "botanical-sage": ["sage green", "greenery", "leafy", "sage"],
    "botanical-terracotta": ["terracotta", "boho", "rust", "earthy tones"],
    "modern-navy": ["navy", "modern navy", "navy and gold modern"],
    "modern-mono": ["black and white", "minimal", "monochrome", "minimalist"],
    "party-candy": ["colorful confetti", "bright and fun", "rainbow", "candy colors"],
    "party-ocean": ["ocean blue", "beachy", "under the sea", "blue confetti"],
}
EVENT_WORDS = {
    "wedding": ["wedding", "wedding invite", "nikkah", "wedding invitation", "marriage ceremony"],
    "engagement": ["engagement party", "engagement", "mangni"],
    "anniversary": ["anniversary party", "anniversary", "anniversary dinner"],
    "birthday": ["birthday party", "bday", "birthday", "b-day bash"],
    "baby_shower": ["baby shower", "babyshower", "shower for the baby"],
}
CHATTER = ["", "", "", "thanks so much!", "Thank you!!", "pls make it pretty :)", "can't wait to see it",
           "hope this is enough info", "Thanks in advance", "😊", "need these asap thanks"]


def _name(rng: random.Random) -> str:
    n = rng.choice(FIRST)
    return f"{n} {rng.choice(LAST)}" if rng.random() < 0.2 and " " not in n else n


def random_order(rng: random.Random, order_date: dt.date) -> tuple[Order, dict]:
    event = rng.choices(list(EVENT_WORDS), weights=[4, 2, 1.5, 3, 1.5])[0]
    if event in ("wedding", "engagement", "anniversary"):
        names = [_name(rng), _name(rng)]
    elif event == "birthday":
        names = [_name(rng)] if rng.random() < 0.9 else [_name(rng), _name(rng)]
    else:
        names = [_name(rng)] if rng.random() < 0.6 else [_name(rng), _name(rng)]
    names = list(dict.fromkeys(names)) if len(set(names)) == len(names) else [names[0]]
    date = order_date + dt.timedelta(days=rng.randint(14, 420))
    time = None if rng.random() < 0.12 else f"{rng.choice([11, 12, 13, 14, 15, 16, 17, 18, 19, 20])}:{rng.choice(['00', '00', '30', '15', '45'])}"
    venue = rng.choice(VENUES) if rng.random() < 0.95 else None
    city = rng.choice(CITIES) if rng.random() < 0.8 else None
    headline = rng.choice(HEADLINES[event]) if rng.random() < 0.45 else None
    age = rng.choice([1, 2, 3, 5, 7, 10, 16, 18, 21, 30, 40, 50, 60, 75]) if event == "birthday" and rng.random() < 0.7 else None
    rsvp = None
    if rng.random() < 0.4:
        rsvp = rng.choice(RSVP).format(a=rng.choice(FIRST), p=rng.choice(PHONES),
                                       d=(date - dt.timedelta(days=rng.randint(10, 40))).strftime("%B %-d"))
    theme, hint = None, None
    if rng.random() < 0.6:
        theme = rng.choice(list(THEME_HINTS))
        hint = rng.choice(THEME_HINTS[theme])
    order = Order(event, names, date.isoformat(), time, venue, city, headline, age, rsvp,
                  theme or DEFAULT_THEME[event])
    return order, {"hint": hint, "event_word": rng.choice(EVENT_WORDS[event])}


# ---------- surface forms ----------

def say_date(d: dt.date, order_date: dt.date, rng: random.Random) -> str:
    # The year may be left out only when "next occurrence after the order date" is unambiguous.
    can_drop_year = d.year == order_date.year or (d.year == order_date.year + 1 and (d.month, d.day) < (order_date.month, order_date.day))
    day = d.day
    suf = "th" if 11 <= day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    forms = [f"{d:%B} {day}, {d.year}", f"{day}{suf} {d:%B} {d.year}", f"{d:%d/%m/%Y}", f"{d.isoformat()}",
             f"{d:%b} {day} {d.year}", f"{d:%A} {day}{suf} {d:%B} {d.year}", f"{day}-{d:%b}-{d.year}",
             f"the {day}{suf} of {d:%B}, {d.year}"]
    if can_drop_year:
        forms += [f"{d:%B} {day}", f"{day}{suf} {d:%B}", f"{d:%a} {day} {d:%b}", f"{d:%B} {day}{suf}"]
    s = rng.choice(forms)
    return s.lower() if rng.random() < 0.25 else s


def say_time(t: str, rng: random.Random) -> str:
    h, m = (int(x) for x in t.split(":"))
    h12 = (h % 12) or 12
    ap = "am" if h < 12 else "pm"
    forms = [f"{t}", f"{h12}:{m:02d} {ap.upper()}", f"{h12}:{m:02d}{ap}", f"{h12}.{m:02d}{ap}"]
    if m == 0:
        forms += [f"{h12}{ap}", f"{h12} {ap}", f"{h12} o'clock" + (" pm" if h >= 12 else ""),
                  f"{h12} in the {'morning' if h < 12 else 'afternoon' if h < 17 else 'evening'}"]
    if m == 30:
        forms += [f"half past {h12} {ap}"]
    return rng.choice(forms)


def say_names(names: list[str], rng: random.Random) -> str:
    joiner = rng.choice([" & ", " and ", " + ", " & "])
    out = joiner.join(names)
    simple = all(n == n.title() and "'" not in n for n in names)
    return out.lower() if simple and rng.random() < 0.15 else out


def _parts(o: Order, meta: dict, od: dt.date, rng: random.Random) -> dict:
    d = dt.date.fromisoformat(o.date)
    return {
        "names": say_names(o.names, rng),
        "event": meta["event_word"],
        "date": say_date(d, od, rng),
        "time": say_time(o.time, rng) if o.time else None,
        "venue": o.venue, "city": o.city, "headline": o.headline, "rsvp": o.rsvp,
        "age": o.age, "hint": meta["hint"], "chatter": rng.choice(CHATTER),
    }


def _where(p):
    if p["venue"] and p["city"]:
        return f"{p['venue']}, {p['city']}"
    return p["venue"] or (f"somewhere in {p['city']}" if p["city"] else None)


def _age_phrase(p, rng):
    if not p["age"]:
        return ""
    a = p["age"]
    suf = "th" if 11 <= a % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(a % 10, "th")
    return rng.choice([f"turning {a}", f"{a}{suf} birthday", f"{a}{suf}", f"they'll be {a}"])


def style_sentence(p, rng):
    s = f"Hi! This is for the {p['event']} of {p['names']}"
    if p["age"]:
        s += f" ({_age_phrase(p, rng)})"
    s += f" on {p['date']}"
    if p["time"]:
        s += f" at {p['time']}"
    w = _where(p)
    if w:
        s += f", venue is {w}" if p["venue"] else f", {w}"
    s += "."
    if p["headline"]:
        s += f' Please put "{p["headline"]}" at the top.'
    if p["rsvp"]:
        s += f" Bottom line: {p['rsvp']}."
    if p["hint"]:
        s += f" We'd love {p['hint']} colors."
    return s + " " + p["chatter"]


def style_form(p, rng):
    lines = [f"Names: {p['names']}", f"Event: {p['event']}", f"Date: {p['date']}"]
    if p["age"]:
        lines.append(f"Age: {p['age']}")
    if p["time"]:
        lines.append(f"Time: {p['time']}")
    if p["venue"]:
        lines.append(f"Venue: {p['venue']}")
    if p["city"]:
        lines.append(f"City: {p['city']}")
    if p["headline"]:
        lines.append(f"Top text: {p['headline']}")
    if p["rsvp"]:
        lines.append(f"RSVP line: {p['rsvp']}")
    if p["hint"]:
        lines.append(f"Colors: {p['hint']}")
    rng.shuffle(lines[3:])
    return "\n".join(lines)


def style_terse(p, rng):
    bits = [p["names"], p["event"]]
    if p["age"]:
        bits.append(_age_phrase(p, rng))
    bits += [p["date"], p["time"], p["venue"], p["city"]]
    if p["headline"]:
        bits.append(f'"{p["headline"]}"')
    if p["rsvp"]:
        bits.append(p["rsvp"])
    if p["hint"]:
        bits.append(p["hint"])
    return " / ".join(b for b in bits if b)


def style_bullets(p, rng):
    out = [f"- {p['event']} for {p['names']}"]
    if p["age"]:
        out.append(f"- {_age_phrase(p, rng)}")
    out.append(f"- when: {p['date']}" + (f" @ {p['time']}" if p["time"] else ""))
    w = _where(p)
    if w:
        out.append(f"- where: {w}")
    if p["headline"]:
        out.append(f"- heading: {p['headline']}")
    if p["rsvp"]:
        out.append(f"- {p['rsvp']}")
    if p["hint"]:
        out.append(f"- theme: {p['hint']}")
    return "\n".join(out)


def style_parent(p, rng):
    s = f"my {'kids' if p['event'] in EVENT_WORDS['birthday'] else 'family'} {p['event']}!! "
    s += f"{p['names']}" + (f" is {_age_phrase(p, rng)}" if p["age"] else "")
    s += f". its on {p['date']}"
    if p["time"]:
        s += f", starts {p['time']}"
    if p["venue"]:
        s += f" at {p['venue']}"
    if p["city"]:
        s += f" in {p['city']}"
    if p["headline"]:
        s += f'. heading should say "{p["headline"]}"'
    if p["rsvp"]:
        s += f". also add: {p['rsvp']}"
    if p["hint"]:
        s += f". going for a {p['hint']} look"
    return s + ". " + p["chatter"]


def style_reversed(p, rng):
    s = ""
    if p["hint"]:
        s += f"Theme {p['hint']}. "
    w = _where(p)
    if w:
        s += f"Location: {w}. "
    s += f"Date {p['date']}" + (f", {p['time']}" if p["time"] else "") + ". "
    s += f"{p['event'].capitalize()} — {p['names']}"
    if p["age"]:
        s += f", {_age_phrase(p, rng)}"
    s += "."
    if p["headline"]:
        s += f' Header: "{p["headline"]}".'
    if p["rsvp"]:
        s += f" {p['rsvp']}."
    return s


# --- held-out styles (never seen in training) ---

def style_email(p, rng):
    s = f"Dear seller,\n\nI would like to order invitations for a {p['event']}. "
    s += f"The {'couple' if ' & ' in p['names'] or ' and ' in p['names'] else 'guest of honour'} is {p['names']}"
    if p["age"]:
        s += f" ({_age_phrase(p, rng)})"
    s += f". It will take place on {p['date']}"
    if p["time"]:
        s += f", beginning at {p['time']}"
    if p["venue"]:
        s += f", at {p['venue']}"
    if p["city"]:
        s += f" ({p['city']})"
    s += "."
    if p["headline"]:
        s += f" Could the card open with the words '{p['headline']}'?"
    if p["rsvp"]:
        s += f" Please include: {p['rsvp']}."
    if p["hint"]:
        s += f" My preference is {p['hint']}."
    return s + "\n\nKind regards"


def style_kv_inline(p, rng):
    kv = [f"who={p['names']}", f"what={p['event']}", f"date={p['date']}"]
    if p["age"]:
        kv.append(f"age={p['age']}")
    if p["time"]:
        kv.append(f"time={p['time']}")
    if p["venue"]:
        kv.append(f"place={p['venue']}")
    if p["city"]:
        kv.append(f"city={p['city']}")
    if p["headline"]:
        kv.append(f"title={p['headline']}")
    if p["rsvp"]:
        kv.append(f"footer={p['rsvp']}")
    if p["hint"]:
        kv.append(f"palette={p['hint']}")
    return "; ".join(kv)


def style_story(p, rng):
    s = f"So we're finally doing it — the {p['event']}! "
    s += f"Celebrating {p['names']}"
    if p["age"]:
        s += f" who's {_age_phrase(p, rng)}"
    s += "."
    if p["venue"]:
        s += f" Everyone's coming to {p['venue']}"
        s += f" in {p['city']}" if p["city"] else ""
        s += "."
    elif p["city"]:
        s += f" It's in {p['city']}."
    s += f" Mark {p['date']}"
    s += f", kick-off {p['time']}." if p["time"] else "."
    if p["headline"]:
        s += f" Big text up top: {p['headline']}."
    if p["rsvp"]:
        s += f" Small print: {p['rsvp']}."
    if p["hint"]:
        s += f" Vibe: {p['hint']}."
    return s + " " + p["chatter"]


TRAIN_STYLES = [style_sentence, style_form, style_terse, style_bullets, style_parent, style_reversed]
TEST_STYLES = [style_email, style_kv_inline, style_story]


def make_example(rng: random.Random, styles) -> dict:
    od = dt.date(2026, 9, 1) + dt.timedelta(days=rng.randint(0, 60))
    order, meta = random_order(rng, od)
    text = rng.choice(styles)(_parts(order, meta, od, rng), rng).strip()
    return {"order_date": od.isoformat(), "text": text, "target": order.as_dict()}
