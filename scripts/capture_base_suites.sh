#!/usr/bin/env bash
# Capture the base-model reference outputs for the stage-comparison suites.
# Run this once before any training starts. Writes data/captures/base_*.jsonl,
# which become the "before" side of every stage comparison (Gate 2 evidence).
#
# Usage: bash scripts/capture_base_suites.sh
# Takes roughly an hour on the dev machine. Safe to leave running; each record
# is flushed as it completes, so an interruption keeps partial progress.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODEL="model/Qwen3-1.7B-Q4_K_M.gguf"
LABEL="base-qwen3-1.7b"
export PATH="$ROOT/tools/llama.cpp-src/build/bin:$PATH"

mkdir -p data/captures

echo "=== 1/3 paraphrase suite (100 prompts) ==="
uv run python scripts/run_baseline.py --model "$MODEL" \
  --prompts data/eval/paraphrase_suite.jsonl \
  --out data/captures/base_paraphrase.jsonl \
  --label "$LABEL" --start-server

echo
echo "=== 2/3 coach eval (15 prompts) ==="
uv run python scripts/run_baseline.py --model "$MODEL" \
  --prompts data/eval/coach_eval.jsonl \
  --out data/captures/base_coach.jsonl \
  --label "$LABEL" --start-server

echo
echo "=== 3/3 multi-turn suite (10 conversations, 32 turns) ==="
uv run python scripts/run_multiturn.py --model "$MODEL" \
  --suite data/eval/multiturn_suite.jsonl \
  --out data/captures/base_multiturn.jsonl \
  --label "$LABEL" --start-server

echo
echo "done. captures:"
ls -lh data/captures/base_*.jsonl
