"""Build train/valid (training styles) and two test sets: seen styles and held-out styles."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from invite_studio.datagen import TEST_STYLES, TRAIN_STYLES, make_example
from invite_studio.prompt import messages

root = Path(__file__).resolve().parent.parent / "data"
(root / "sft").mkdir(parents=True, exist_ok=True)
rng = random.Random(7)
splits = {"train": (1500, TRAIN_STYLES), "valid": (100, TRAIN_STYLES),
          "test_seen": (100, TRAIN_STYLES), "test_heldout": (200, TEST_STYLES)}
for name, (n, styles) in splits.items():
    exs = [make_example(rng, styles) for _ in range(n)]
    (root / f"{name}.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in exs))
    if name in ("train", "valid"):
        (root / "sft" / f"{name}.jsonl").write_text(
            "".join(json.dumps({"messages": messages(e)}, ensure_ascii=False) + "\n" for e in exs))
    print(name, len(exs))
