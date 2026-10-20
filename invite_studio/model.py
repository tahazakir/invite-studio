"""Run the (fine-tuned) extractor with per-field confidence from token probabilities."""
from __future__ import annotations

import json
import re
from functools import lru_cache

import mlx.core as mx
from mlx_lm import load, stream_generate

from .prompt import messages

BASE = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
KEY_RE = re.compile(r'"(\w+)":\s*$')


@lru_cache(maxsize=4)
def get(adapter: str | None):
    return load(BASE, adapter_path=adapter) if adapter else load(BASE)


def extract(text: str, order_date: str, adapter: str | None = "adapters", shots: list[dict] | None = None,
            max_tokens: int = 220) -> dict:
    model, tok = get(adapter)
    msgs = messages({"order_date": order_date, "text": text}, with_answer=False)
    if shots:
        fewshot = []
        for s in shots:
            fewshot += messages(s)[1:]
        msgs = msgs[:1] + fewshot + msgs[1:]
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    out, field_probs, key = "", {}, None
    for r in stream_generate(model, tok, prompt, max_tokens=max_tokens):
        p = float(mx.exp(r.logprobs[r.token]).item())
        if m := KEY_RE.search(out):
            key = m[1]
        if key and r.text.strip() not in ("", ",", "}", ":"):
            field_probs.setdefault(key, []).append(p)
        out += r.text
        if out.rstrip().endswith("}") and out.count("{") == out.count("}"):
            break
    try:
        data = json.loads(out[out.index("{"): out.rindex("}") + 1])
        valid = True
    except ValueError:
        data, valid = {}, False
    conf = {k: round(min(v), 4) for k, v in field_probs.items()}
    return {"raw": out, "json_valid": valid, "fields": data, "field_conf": conf,
            "min_conf": min(conf.values()) if conf else 0.0}
