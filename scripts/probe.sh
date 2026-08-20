#!/usr/bin/env bash
set -euo pipefail
MODEL="${1:?usage: probe.sh path/to/model.gguf 'question text'}"
QUESTION="${2:?usage: probe.sh path/to/model.gguf 'question text'}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"

printf 'You are a Nigerian tax assistant. Answer briefly and directly.\n\nUser: %s\nAssistant:' "$QUESTION" > /tmp/opencode/probe_prompt.txt

timeout 300 "$ROOT/tools/llama.cpp-src/build/bin/llama-cli" \
  -m "$MODEL" \
  -f /tmp/opencode/probe_prompt.txt \
  -n 150 -t 4 --temp 0.2 -c 512 \
  --no-display-prompt -st 2>/dev/null | tr -c '[:print:]\n' ' ' | sed 's/  */ /g' | grep -v "^ $" | tail -12
