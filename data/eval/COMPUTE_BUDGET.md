# Compute Budget — Qwen3-1.7B Pipeline (rough, pre-measurement)

Estimates for scheduling the $50 AGH credits and any Colab fallback. Token
counts are approximate (English ~4 chars/token); wall-clock ranges assume:

- **T4 16 GB (Colab or AGH small GPU):** QLoRA 1.7B at ~1.5–3K training tokens/s
- **AGH modern GPU (A100/L40S/4090-class):** ~3–10K training tokens/s
- GRPO is generation-bound; ranges are wide until the smoke test measures it.

| Stage | Workload | Tokens (approx) | T4 wall-clock | AGH wall-clock |
|---|---|---|---|---|
| Smoke test | load + 8 steps + imports | negligible | 10–20 min (installs) | 10–15 min |
| **DAPT** | 175K corpus + 15% replay, 2 epochs | ~400K | 15–30 min | 5–10 min |
| **SFT R1** | ~1.1M tokens/epoch, 3 epochs (3–5K examples) | ~3.3M | 30–60 min | 10–25 min |
| **KTO** | ~2–3K preference pairs, 1 epoch | ~1.5–2M | 30–60 min | 10–20 min |
| **GRPO** | 500–2,000 prompts × 4–8 generations | 1–4M generated + updates | 2–6 h | 1–3 h |
| Merges + GGUF | 3–5 conversions across stages | — | 10–30 min each | 5–15 min each |
| Eval captures | 4 suites × stages (CPU or GPU) | — | 1–1.5 h per stage (CPU local) | minutes if GPU |

**Planning total:** T4-only ≈ 6–12 GPU-hours; AGH ≈ 2.5–6 GPU-hours plus eval
overhead. At typical Africa GPU Hub pricing this fits the $50 credit with
room for retries; keep a 2× contingency for SFT/KTO iterations.

## Where the credits should go

1. **Unsloth smoke test first** (validates environment, measures tokens/s).
2. **DAPT + SFT** (highest value per GPU-hour; both are small).
3. **KTO** (cheap, similar to SFT).
4. **GRPO last** and smallest (most expensive; only after SFT/KTO behavior is accepted).
5. Never spend GPU time on base captures or GGUF conversions that
   `llama.cpp`/CPU can do locally.

## What to record after each run (for the re-estimate)

- `tokens/s` and wall-clock from `scripts/unsloth_smoke_test.py` and `dapt_run.json`
- `dapt_run.json`, SFT/KTO/GRPO run logs → `data/captures/` or the training output dirs
- Actual eval capture time on the dev machine (the base run gives the reference)

Re-measure after the smoke test and update this table with real numbers — these
are order-of-magnitude estimates, not measurements.
