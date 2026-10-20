"""Feedback loop: fold human corrections from the review queue into the training set and retrain.

Corrections are upsampled because each one is a real failure on a real order, which is
worth more than a synthetic example. Usage: uv run python scripts/retrain.py [--upsample 5]
"""
import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from invite_studio.prompt import messages  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--upsample", type=int, default=5)
ap.add_argument("--iters", type=int, default=200)
ap.add_argument("--out", default="adapters_v2")
a = ap.parse_args()

corr_path = ROOT / "data" / "corrections.jsonl"
corr = [json.loads(l) for l in corr_path.read_text().splitlines()] if corr_path.exists() else []
if not corr:
    sys.exit("No corrections yet: review some orders in the UI first.")
train = [json.loads(l) for l in (ROOT / "data" / "sft" / "train.jsonl").read_text().splitlines()]
new = [{"messages": messages(c)} for c in corr] * a.upsample
rows = train + new
random.Random(0).shuffle(rows)
out = ROOT / "data" / "sft_v2"
out.mkdir(exist_ok=True)
(out / "train.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
(out / "valid.jsonl").write_text((ROOT / "data" / "sft" / "valid.jsonl").read_text())
print(f"{len(train)} synthetic + {len(corr)} corrections x{a.upsample} -> {out}")
subprocess.run([str(ROOT / "scripts" / "train.sh"), str(out), a.out], check=True,
               env={**os.environ, "ITERS": str(a.iters)})
print(f"Done. Evaluate with: uv run python scripts/evaluate.py --methods finetuned --adapter {a.out}")
