"""Prompt format shared by training, evaluation, and serving."""
import json

SYSTEM = ("You convert a customer's free-text invitation order into JSON with keys "
          "event_type, names, date, time, venue, city, headline, age, rsvp, theme. "
          "event_type is one of wedding, engagement, anniversary, birthday, baby_shower. "
          "names is a list of properly capitalized names. date is YYYY-MM-DD (if the year is missing, "
          "use the next occurrence after the order date). time is 24-hour HH:MM. Copy venue, city, "
          "headline, and rsvp text exactly. theme is one of classic-gold, classic-blush, botanical-sage, "
          "botanical-terracotta, modern-navy, modern-mono, party-candy, party-ocean, chosen from the "
          "customer's color or style words, or the default for the event when none are given. "
          "Use null for anything not provided. Output only the JSON.")


def user_msg(order_date: str, text: str) -> str:
    return f"Order date: {order_date}\nPersonalization:\n{text}"


def target_json(target: dict) -> str:
    keys = ["event_type", "names", "date", "time", "venue", "city", "headline", "age", "rsvp", "theme"]
    return json.dumps({k: target.get(k) for k in keys}, ensure_ascii=False)


def messages(ex: dict, with_answer: bool = True) -> list[dict]:
    m = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_msg(ex["order_date"], ex["text"])}]
    if with_answer:
        m.append({"role": "assistant", "content": target_json(ex["target"])})
    return m
