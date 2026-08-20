#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:?usage: bench.sh path/to/model.gguf}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"

BENCH_BIN="${BENCH_BIN:-$ROOT/tools/llama.cpp-src/build/bin/llama-bench}"
if [[ ! -x "$BENCH_BIN" ]]; then
  BENCH_BIN="$ROOT/tools/llama-b10434/llama-bench"
fi

mkdir -p "$HERE/results"
NAME="$(basename "$MODEL" .gguf)"
OUT="$HERE/results/${NAME}.json"

"$BENCH_BIN" \
  -m "$MODEL" \
  -p 512 \
  -n 128 \
  -ngl 0 \
  -t 4 \
  --output json > "$OUT"

echo "results: $OUT"
"$ROOT/.venv/bin/python" - "$OUT" <<'EOF'
import json, sys
rows = json.load(open(sys.argv[1]))
pp = next((r for r in rows if r.get("n_gen", 0) == 0 and r.get("n_prompt", 0) > 0), None)
tg = next((r for r in rows if r.get("n_gen", 0) > 0), None)
print(f"prompt processing: {pp['avg_ts']:.2f} t/s" if pp else "pp: n/a")
print(f"generation (tg):   {tg['avg_ts']:.2f} t/s" if tg else "tg: n/a")
EOF
