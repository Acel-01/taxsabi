#!/usr/bin/env bash
# Provision the training environment on a fresh GPU instance (AGH/Shadeform/Colab-like).
#
# Why: generic cloud images ship old system Python (3.10 + apt-era numpy/Pillow)
# which conflicts with the modern ML stack. A uv-managed Python 3.12 venv avoids
# the system libraries entirely and selects CUDA-matched torch wheels.
#
# Usage:
#   bash scripts/setup_training_env.sh            # default CUDA 12.8 backend
#   bash scripts/setup_training_env.sh cu130      # if the driver supports CUDA 13
set -euo pipefail

BACKEND="${1:-cu128}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "creating isolated Python 3.12 environment..."
uv python install 3.12
uv venv .venv --python 3.12
# shellcheck disable=SC1091
source .venv/bin/activate

echo "installing unsloth + CUDA-matched torch (backend: $BACKEND)..."
uv pip install --torch-backend="$BACKEND" unsloth

python - <<'PY'
import torch
print(f"torch {torch.__version__} | cuda available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"gpu: {torch.cuda.get_device_name(0)}")
else:
    raise SystemExit("CUDA not available - check the driver / torch backend")
PY

echo
echo "environment ready. activate with: source .venv/bin/activate"
echo "then verify with: python scripts/unsloth_smoke_test.py"
