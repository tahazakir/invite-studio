#!/usr/bin/env bash
# LoRA fine-tune of Qwen2.5-1.5B-Instruct (4-bit) on Apple silicon with MLX.
set -euo pipefail
cd "$(dirname "$0")/.."
DATA="${1:-data/sft}"
ADAPTERS="${2:-adapters}"
uv run mlx_lm.lora \
  --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
  --train --data "$DATA" --adapter-path "$ADAPTERS" \
  --fine-tune-type lora --num-layers 16 --mask-prompt \
  --batch-size 4 --iters "${ITERS:-600}" --learning-rate 1e-4 \
  --steps-per-eval 100 --val-batches 25 --save-every 200 \
  --max-seq-length 1024 --grad-checkpoint
