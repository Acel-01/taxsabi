#!/usr/bin/env bash
# TaxSabi launcher — Linux/macOS
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

MODEL="$HERE/../model/TaxSabi-Qwen3-1.7B-Q8_0.gguf"

SERVER="$HERE/bin/llama-server"
LIBS="$HERE/bin"
if [[ ! -x "$SERVER" ]]; then
  SERVER="$HERE/../tools/llama.cpp-src/build/bin/llama-server"
  LIBS="$HERE/../tools/llama.cpp-src/build/bin"
fi

if [[ ! -x "$SERVER" ]]; then
  echo "[!] Missing llama-server (app/bin or tools/llama.cpp-src/build/bin)"
  echo "    Build llama.cpp or copy the llama-server binary into app/bin/."
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "[!] Missing $MODEL"
  echo "    Run ../download_model.sh (or copy the GGUF into model/)."
  exit 1
fi

echo "Starting the TaxSabi engine (Qwen3-1.7B Q8_0)..."
export LD_LIBRARY_PATH="$LIBS:${LD_LIBRARY_PATH:-}"
"$SERVER" \
  -m "$MODEL" \
  -c 2048 -t 4 --port 8080 --temp 0 --jinja --no-webui &
SERVER_PID=$!
echo $SERVER_PID > .server.pid

echo "Waiting for the engine to load..."
sleep 4

( xdg-open TaxSabi.html 2>/dev/null || open TaxSabi.html 2>/dev/null ) \
  || echo "Open TaxSabi.html in your browser."

echo
echo "TaxSabi is running (engine PID $SERVER_PID)."
echo "Stop it with: ./stop-taxsabi.sh"
