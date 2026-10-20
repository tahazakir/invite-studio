"""Order intake: extract fields, render, check, and route to auto-approve or human review."""
from __future__ import annotations

from .checks import run_checks
from .layout import render
from .schema import Order

# Chosen on the seen-style test set by scripts/evaluate.py (see data/eval/summary.md).
CONF_THRESHOLD = 0.92


def decide(checks: list[dict], json_valid: bool, min_conf: float | None, threshold: float = CONF_THRESHOLD) -> dict:
    failed = [c["check"] for c in checks if not c["ok"]]
    reasons = []
    if not json_valid:
        reasons.append("model output was not valid JSON")
    reasons += [f"check failed: {f}" for f in failed]
    if min_conf is not None and min_conf < threshold:
        reasons.append(f"low model confidence ({min_conf:.2f} < {threshold:.2f})")
    return {"route": "auto_approve" if not reasons else "review", "reasons": reasons}


def build(fields: dict, text: str | None, order_date: str | None, theme: str | None = None) -> dict:
    order = Order.from_dict(fields)
    try:
        svg, report = render(order, theme)
    except Exception as e:  # noqa: BLE001 - a broken order must land in review, not crash intake
        return {"order": order.as_dict(), "svg": None, "report": None,
                "checks": [{"check": "render", "ok": False, "detail": str(e)}]}
    checks = run_checks(order, svg, report, text, order_date)
    return {"order": order.as_dict(), "svg": svg, "report": report, "checks": checks}
