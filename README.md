# TaxSabi

ADTC 2026 — Laptop LLM Challenge, Corporate/Enterprise track.

A fully offline Nigerian personal-income-tax assistant: a fine-tuned GGUF model that answers 2026 tax-band, relief, calculation, and what-if questions in English and Nigerian Pidgin. A deterministic Decimal-based rules engine verifies every training example against the Nigeria Tax Act 2025, so the model learns from engine-guaranteed arithmetic.

The scored artifact is the raw GGUF (`model/TaxSabi-Qwen3-1.7B-Q8_0.gguf`), downloaded by `download_model.sh` and run through llama.cpp. No application layer is invoked at evaluation time.

- Project overview: `PROJECT.md`
- Technical report (incl. Model Provenance): `REPORT.md`
- Proof of training (adapter, scripts, logs, checksums): `provenance/`
- Verified source register: `sources/SOURCE_REGISTER.md`
- Development plan and Gate 2 outcome: `DEVELOPMENT_PLAN.md`

## Submission checklist (Gate 2)

- Repository is **public** on GitHub
- `metadata.json` is fully filled in — exactly **2 test prompts** plus the Gate 2 `provenance` object
- `download_model.sh` declares a **static, pinned** model URL and downloads to `model/` without credentials, idempotently
- The downloaded file is a valid **GGUF** weight file
- `model/*.gguf` is gitignored — weights are not committed
- `REPORT.md` includes the **Model Provenance** section and a before/after comparison
- `provenance/` contains the final adapter (Git LFS), training scripts, run logs, dataset documentation, checksums and merge/quantization notes
- The model runs entirely **offline** — zero external network calls during inference
- Runtime is **llama.cpp** only
- Runs within the 8 GB RAM / 7 GB budget laptop profile (~1.9 GB peak RSS measured)

## Quickstart

```bash
# download the submission model (idempotent, no credentials)
bash download_model.sh

# run the official profiler in participant mode
python3 -m pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
adtc-profiler run --submission . --mode participant --output submission.json

# chat with the model
llama-cli -m model/TaxSabi-Qwen3-1.7B-Q8_0.gguf \
  -cnv --jinja -t 4 -c 2048 --temp 0 \
  -sys "You are an assistant that answers questions about Nigerian individual income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."

# rules engine self-test
uv run python src/rules_engine/test_engine.py
```

## Layout

| Path | Purpose |
|---|---|
| `sources/` | Extracted statute text + verified source register (F-001…F-019) |
| `src/rules_engine/` | Deterministic 2026 tax calculator (dataset verifier) |
| `data/` | SFT/KTO/GRPO datasets, eval suites, capture evidence |
| `scripts/` | Data generation, verification, QLoRA training, evaluation |
| `provenance/` | Gate 2 proof-of-training package (adapter, scripts, logs, checksums) |
| `reports/` | Stage comparison reports and profiler benchmarks |
| `bench/` | llama-bench scripts and results |
| `model/` | Downloaded submission GGUF (gitignored) |

## The model

- **Base:** Qwen3-1.7B (`unsloth/Qwen3-1.7B` @ `6262b50d6c1f8ee5e4ac750d710c33603bfc2a0c`, Apache 2.0)
- **Pipeline:** DAPT → SFT → KTO → GRPO, all QLoRA via Unsloth (see `provenance/training_log.txt`)
- **Training data:** 1,929 engine-verified SFT examples; 3,144 KTO binary labels; engine-grounded GRPO prompt pools — every naira figure is engine-computed (`provenance/dataset_info.md`)
- **Quantization:** GGUF **Q8_0**, 1.70 GiB. Q4_K_M, Q5_K_M and Q6_K were exported and tested but rejected: Q4/Q6 corrupt the 2026 band table (and Q4 flips arithmetic), Q5 substitutes an older table; Q8_0 matches the full-precision model on the held-out (5/10), dev (8/9) and band-phrasing comparisons (`provenance/merge_quantize.md`)
- **Measured (participant profiler, i5-8250U, 4 threads):** 3.3–4.7 t/s generation, ~1.94 GB peak RSS, `Sperf` 22–31, `Seff` ~73, no throttling detected
- **Evaluation:** held-out probe 5/10 exact final tax (7/10 chargeable income); dev probe 8/9; paraphrase suite 17/40 exact with 5/8 phrasing groups consistent; zero out-of-register citations across 1,010 captured outputs

## Reproducing the pipeline

Training pipeline (GPU): `scripts/dapt_pretrain.py` → `scripts/finetune_qlora.py` → `scripts/kto_train.py` → `scripts/grpo_train.py`.
Data pipeline: `scripts/build_sft_jobs.py`, `scripts/build_kto_prompts.py`, `scripts/build_grpo_pool.py`, verified by `scripts/verify_sft_generation.py`.
Exact commands, hyperparameters and the merge/quantization steps: `provenance/training_log.txt` and `provenance/merge_quantize.md`.

## License

Model weights derive from Qwen3-1.7B (Apache 2.0). OASST1 replay data is Apache-2.0; the statutes are public government gazettes. Repository code follows the ADTC submission template (GPL-3.0).
