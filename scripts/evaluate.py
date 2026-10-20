"""Compare regex rules, a prompted base model (2-shot), and the LoRA fine-tune.

Reports field accuracy, full-order accuracy, and the review policy's trade-off:
how many orders ship automatically and how many of those are fully correct.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from invite_studio import rules  # noqa: E402
from invite_studio.pipeline import build, decide  # noqa: E402
from invite_studio.schema import FIELDS, Order  # noqa: E402

OUT = ROOT / "data" / "eval"


def load(name, n=None):
    rows = [json.loads(l) for l in (ROOT / "data" / f"{name}.jsonl").read_text().splitlines()]
    return rows[:n] if n else rows


def norm(v):
    return None if v in ("", [], None) else v


def score(pred: dict, gold: dict) -> dict:
    p = Order.from_dict(pred).as_dict() if pred else {}
    return {f: norm(p.get(f)) == norm(gold.get(f)) for f in FIELDS}


def run(method, rows, adapter="adapters"):
    from invite_studio import model as M
    shots = load("train", 2) if method == "base_2shot" else None
    res = []
    t0 = time.time()
    for i, ex in enumerate(rows):
        if method == "rules":
            fields, valid, conf, fconf = rules.parse(ex["text"], ex["order_date"]), True, None, {}
        else:
            r = M.extract(ex["text"], ex["order_date"], adapter=None if method == "base_2shot" else adapter, shots=shots)
            fields, valid, conf, fconf = r["fields"], r["json_valid"], r["min_conf"], r["field_conf"]
        out = build(fields, ex["text"], ex["order_date"]) if valid else {"checks": []}
        sc = score(fields if valid else {}, ex["target"])
        res.append({"text": ex["text"], "gold": ex["target"], "pred": fields, "json_valid": valid,
                    "min_conf": conf, "field_conf": fconf, "fields_ok": sc, "all_ok": all(sc.values()),
                    "checks": out["checks"]})
        if (i + 1) % 25 == 0:
            print(f"  {method}: {i + 1}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)
    return res


def policy(res, thr):
    approved = [r for r in res if decide(r["checks"], r["json_valid"], r["min_conf"], thr)["route"] == "auto_approve"]
    wrong = [r for r in res if not r["all_ok"]]
    caught = [r for r in wrong if r not in approved]
    return {"auto_approve_rate": len(approved) / len(res),
            "approved_accuracy": sum(r["all_ok"] for r in approved) / len(approved) if approved else None,
            "errors_caught": len(caught) / len(wrong) if wrong else None}


def summarize(res):
    n = len(res)
    return {"n": n, "json_valid": sum(r["json_valid"] for r in res) / n,
            "order_exact": sum(r["all_ok"] for r in res) / n,
            "fields": {f: sum(r["fields_ok"][f] for r in res) / n for f in FIELDS}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", default="rules,finetuned,base_2shot")
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--adapter", default="adapters")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    all_sum = {}
    for method in a.methods.split(","):
        for split in ("test_seen", "test_heldout"):
            n = a.n or (100 if method == "base_2shot" else None)
            rows = load(split, n)
            print(f"{method} on {split} ({len(rows)})", flush=True)
            res = run(method, rows, a.adapter)
            (OUT / f"{method}_{split}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
            all_sum[f"{method}/{split}"] = summarize(res)

    # Pick the confidence threshold on seen styles: highest auto-approve rate with >= 99% approved accuracy.
    thr = 0.5
    seen_path = OUT / "finetuned_test_seen.json"
    if seen_path.exists():
        seen = json.loads(seen_path.read_text())
        best = None
        for t in [x / 100 for x in range(30, 100, 2)]:
            p = policy(seen, t)
            if p["approved_accuracy"] is not None and p["approved_accuracy"] >= 0.99 and (best is None or p["auto_approve_rate"] > best[1]):
                best = (t, p["auto_approve_rate"])
        thr = best[0] if best else 0.95
    for key in list(all_sum):
        method, split = key.split("/")
        res = json.loads((OUT / f"{method}_{split}.json").read_text())
        all_sum[key]["policy"] = policy(res, thr if method != "rules" else 0)
    all_sum["threshold"] = thr
    (OUT / "summary.json").write_text(json.dumps(all_sum, indent=1))

    lines = [f"# Evaluation\n\nConfidence threshold (picked on seen styles): **{thr:.2f}**\n",
             "| method / split | n | valid JSON | full order exact | names | date | time | venue | theme | auto-approved | accuracy of auto-approved | errors sent to review |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    pct = lambda v: "-" if v is None else f"{v * 100:.1f}%"
    for k, s in all_sum.items():
        if k == "threshold":
            continue
        f, p = s["fields"], s["policy"]
        lines.append(f"| {k} | {s['n']} | {pct(s['json_valid'])} | {pct(s['order_exact'])} | {pct(f['names'])} | {pct(f['date'])} | "
                     f"{pct(f['time'])} | {pct(f['venue'])} | {pct(f['theme'])} | {pct(p['auto_approve_rate'])} | "
                     f"{pct(p['approved_accuracy'])} | {pct(p['errors_caught'])} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
