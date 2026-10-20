from invite_studio.schema import Order, THEMES
from invite_studio.layout import render
from invite_studio.checks import run_checks
from pathlib import Path
out = Path("data/smoke"); out.mkdir(parents=True, exist_ok=True)
orders = [
    Order("wedding", ["Sarah", "Ahmed"], "2027-06-14", "16:00", "The Grand Hall, Pearl Continental", "Lahore", "Together with their families", rsvp="RSVP to Aisha by May 1"),
    Order("birthday", ["Maximilian-Alexander"], "2026-12-05", "14:30", "Funland Trampoline Park", "Karachi", "You're invited!", age=7, rsvp="Text Nadia at 0300 1234567"),
]
for i, o in enumerate(orders):
    for t in THEMES:
        svg, rep = render(o, t)
        (out / f"{i}_{t}.svg").write_text(svg)
        fails = [c for c in run_checks(o, svg, rep) if not c["ok"]]
        print(i, t, {k: (v.get("size"), v.get("lines")) for k, v in rep["slots"].items() if not v.get("empty")}, "FAILS:", fails)
