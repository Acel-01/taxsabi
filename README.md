# TaxSabi

ADTC 2026 — Laptop LLM Challenge, Corporate/Enterprise track.

A fully offline Nigerian personal-income-tax assistant: a fine-tuned GGUF model that answers 2026 tax-band, relief, calculation, and what-if questions in English and Nigerian Pidgin. A deterministic Decimal-based rules engine verifies every training example against the Nigeria Tax Act 2025, so the model learns from engine-guaranteed arithmetic.

The scored artifact is the raw GGUF (`model/qwen2.5-1.5b-v6c.Q4_K_M.gguf`), downloaded by `download_model.sh` and run through llama.cpp. No application layer is invoked at evaluation time.

Project overview: `PROJECT.md`
Technical report: `REPORT.md`
Verified source register: `sources/SOURCE_REGISTER.md`

## Submission checklist

- Repository is **public** on GitHub
- `metadata.json` is fully filled in with exactly **2 test prompts**
- `download_model.sh` downloads the model to `model/` without credentials, idempotently
- The downloaded file is a valid **GGUF** weight file
- `model/*.gguf` is gitignored — weights are not committed
- `REPORT.md` is filled in with the technical writeup
- The model runs entirely **offline** — zero external network calls during inference
- Runtime is **llama.cpp** only
- Runs within the 8 GB RAM / 7 GB budget laptop profile (~1.7 GB peak RSS measured)

## Quickstart

```bash
# download the submission model (idempotent, no credentials)
bash download_model.sh

# run the official profiler
python3 -m pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
adtc-profiler run --submission . --mode participant --output submission.json

# chat with the model
llama-cli \
  -m model/qwen2.5-1.5b-v6c.Q4_K_M.gguf \
  -cnv -t 4 -c 2048 -n 256 --temp 0 \
  -p "I earn NGN 800,000 a year and no deductions or reliefs. How much tax do I pay? Please show the calculation."

# rules engine self-test
uv run python src/rules_engine/test_engine.py
```

## Layout

| Path | Purpose |
|---|---|
| `sources/` | Extracted statute text + verified source register (F-001…F-007) |
| `src/rules_engine/` | Deterministic 2026 tax calculator (dataset verifier) |
| `data/` | Dataset schema, scenarios, and the frozen training candidate |
| `scripts/` | Data generation, verification, QLoRA fine-tuning, and evaluation scripts |
| `bench/` | llama-bench scripts and results |
| `model/` | Downloaded submission GGUF (gitignored) |

## The model

- Base: Qwen2.5-1.5B-Instruct (Apache 2.0), QLoRA fine-tuned (rank 32, 3 epochs, lr 2e-4)
- Training data: `data/train/final_en_pcm_v6c_candidate.jsonl` — 1,411 records (1,362 English, 49 human-reviewed Pidgin), every number engine-verified
- Quantization: GGUF Q4_K_M, 941 MB
- Measured (i5-8250U @ 1.6 GHz, 4 threads, CPU-only): 10.09 t/s generation, ~1.7 GB peak RSS
- Official profiler participant run: 8.83 t/s, 1,691 MB peak RSS, no throttling, `arc_easy(50)` 0.76

## Reproducing the data

```bash
uv run python scripts/generate_scenarios.py
uv run python scripts/render_seed_dataset.py
uv run python scripts/generate_behavior_dataset.py
uv run python scripts/generate_counterfactual_dataset.py
uv run python scripts/generate_targeted_v6.py
uv run python scripts/generate_pidgin_v6c.py
uv run python scripts/strip_preamble.py --input data/train/final_english_v5.jsonl --output data/train/final_english_v5_concise.jsonl
uv run python scripts/assemble_dataset.py \
  --inputs data/train/final_english_v5_concise.jsonl \
           data/train/targeted_v6_english_concise.jsonl \
           data/train/pidgin_train_v5_concise.jsonl \
           data/train/targeted_v6_pidgin_reviewed_concise.jsonl \
           data/train/targeted_v6c_pidgin_reviewed.jsonl \
  --output data/train/final_en_pcm_v6c_candidate.jsonl \
  --max-calculation 1100
```

Cloud-generated records are never trusted until `scripts/verify_dataset.py` passes.

## License

Model weights derive from Qwen2.5-1.5B-Instruct (Apache 2.0). Repository code follows the ADTC submission template (GPL-3.0).
