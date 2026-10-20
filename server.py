"""FastAPI app: order intake, rendering, review queue, corrections, and monitoring."""
from __future__ import annotations

import datetime as dt
import json
import threading
import uuid
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from invite_studio import rules
from invite_studio.layout import audit_library
from invite_studio.pipeline import CONF_THRESHOLD, build, decide
from invite_studio.schema import THEMES

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ORDERS = DATA / "orders.jsonl"
CORRECTIONS = DATA / "corrections.jsonl"
ADAPTER = "adapters"
_lock = threading.Lock()

app = FastAPI(title="Invite Studio")
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")


def _read(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []


def _write_all(path: Path, rows: list[dict]):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


class ProcessIn(BaseModel):
    text: str
    order_date: str | None = None
    method: str = "finetuned"


class RenderIn(BaseModel):
    fields: dict
    text: str | None = None
    order_date: str | None = None
    theme: str | None = None


class ResolveIn(BaseModel):
    fields: dict


@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/samples")
def samples():
    rows = [json.loads(l) for l in (DATA / "test_heldout.jsonl").read_text().splitlines()]
    picks = [rows[i] for i in (0, 3, 7, 12, 21, 30)]
    hand = [
        {"order_date": "2026-10-20", "text": "hiii!! invites for edward & vivian 💍 the nuptials are on the 14th of feb, 7.30pm at The Savoy Ballroom, London. top should say Together with their families. sage green please, my mum loves greenery"},
        {"order_date": "2026-10-20", "text": "Order for my son's party - Bartholomew is turning 5!! Saturday 9 jan 2027, 2pm, Bounce House Party Zone (Karachi). RSVP to Hina at 0321-7654321. bright and fun colours"},
    ]
    return [{"order_date": r["order_date"], "text": r["text"]} for r in hand + picks]


@app.get("/api/library")
def library():
    return {"themes": list(THEMES), "templates": audit_library()}


@app.post("/api/process")
def process(body: ProcessIn):
    order_date = body.order_date or dt.date.today().isoformat()
    if body.method == "rules":
        fields, valid, conf, fconf, raw = rules.parse(body.text, order_date), True, None, {}, None
    else:
        from invite_studio import model as M
        r = M.extract(body.text, order_date, adapter=ADAPTER)
        fields, valid, conf, fconf, raw = r["fields"], r["json_valid"], r["min_conf"], r["field_conf"], r["raw"]
    out = build(fields, body.text, order_date) if valid else {"order": {}, "svg": None, "report": None, "checks": []}
    decision = decide(out["checks"], valid, conf)
    rec = {"id": uuid.uuid4().hex[:8], "created": dt.datetime.now().isoformat(timespec="seconds"),
           "order_date": order_date, "text": body.text, "method": body.method, "model_fields": out["order"],
           "field_conf": fconf, "min_conf": conf, "checks": out["checks"], "route": decision["route"],
           "reasons": decision["reasons"], "status": "approved" if decision["route"] == "auto_approve" else "pending"}
    with _lock, ORDERS.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {**rec, "svg": out["svg"], "report": out["report"], "threshold": CONF_THRESHOLD, "raw": raw}


@app.post("/api/render")
def render_order(body: RenderIn):
    out = build(body.fields, body.text, body.order_date, body.theme)
    return {"svg": out["svg"], "checks": out["checks"], "report": out["report"], "order": out["order"]}


@app.get("/api/queue")
def queue():
    return [o for o in reversed(_read(ORDERS)) if o["status"] == "pending"]


@app.get("/api/orders/{oid}")
def get_order(oid: str):
    for o in _read(ORDERS):
        if o["id"] == oid:
            out = build(o["model_fields"], o["text"], o["order_date"])
            return {**o, "svg": out["svg"], "report": out["report"]}
    raise HTTPException(404)


@app.post("/api/orders/{oid}/resolve")
def resolve(oid: str, body: ResolveIn):
    with _lock:
        rows = _read(ORDERS)
        for o in rows:
            if o["id"] == oid:
                final = build(body.fields, o["text"], o["order_date"])["order"]
                changed = [k for k in final if final[k] != o["model_fields"].get(k)]
                o.update(status="corrected" if changed else "approved", final_fields=final, changed_fields=changed,
                         resolved=dt.datetime.now().isoformat(timespec="seconds"))
                if changed:
                    with CORRECTIONS.open("a") as f:
                        f.write(json.dumps({"order_date": o["order_date"], "text": o["text"], "target": final,
                                            "changed": changed, "order_id": oid}, ensure_ascii=False) + "\n")
                _write_all(ORDERS, rows)
                return o
    raise HTTPException(404)


@app.get("/api/stats")
def stats():
    rows = _read(ORDERS)
    corr = _read(CORRECTIONS)
    fails = Counter("low model confidence" if r.startswith("low model confidence") else r.removeprefix("check failed: ")
                    for o in rows for r in o["reasons"])
    changed = Counter(f for c in corr for f in c["changed"])
    confs = [o["min_conf"] for o in rows if o.get("min_conf") is not None]
    hist = [0] * 10
    for c in confs:
        hist[min(int(c * 10), 9)] += 1
    ev = DATA / "eval" / "summary.json"
    return {
        "total": len(rows),
        "auto_approved": sum(o["route"] == "auto_approve" for o in rows),
        "sent_to_review": sum(o["route"] == "review" for o in rows),
        "pending": sum(o["status"] == "pending" for o in rows),
        "corrected": sum(o["status"] == "corrected" for o in rows),
        "corrections_logged": len(corr),
        "check_failures": dict(fails.most_common()),
        "corrected_fields": dict(changed.most_common()),
        "confidence_hist": hist,
        "threshold": CONF_THRESHOLD,
        "eval": json.loads(ev.read_text()) if ev.exists() else None,
    }
