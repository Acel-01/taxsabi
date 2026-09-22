#!/usr/bin/env bash
if [[ -f .server.pid ]]; then
  kill "$(cat .server.pid)" 2>/dev/null || true
  rm -f .server.pid
fi
pkill -x llama-server 2>/dev/null || true
echo "TaxSabi engine stopped."
