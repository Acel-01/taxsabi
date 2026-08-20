# TaxSabi — Project Overview

An offline Nigerian 2026 personal-income-tax assistant submitted to the ADTC 2026 Laptop LLM Challenge (Corporate/Enterprise track). The scored artifact is a single fine-tuned GGUF run through llama.cpp — no application layer, no network, no GPU.

## What it does

Answers personal-income-tax questions for the Nigeria Tax Act 2025, 2026 year of assessment:

- Tax bands and rates (Fourth Schedule)
- Chargeable income and eligible deductions (section 30(2)(a))
- Rent relief (20% of annual rent, capped at NGN 500,000)
- Pension, NHF, NHIS, mortgage-interest, and life-insurance treatment where verified
- Full calculation walkthroughs, monthly-to-annual income conversion
- What-if scenarios (e.g., increasing a pension contribution)
- Scope behavior: defaults to Nigeria/2026 when omitted; declines other jurisdictions and years
- English and Nigerian Pidgin

## Architecture

```text
Nigeria Tax Act 2025 (extracted text + verified source register)
                          |
                          v
Deterministic Decimal tax rules engine (src/rules_engine/)
                          |
                          v
Engine-verified Q&A training dataset (1,411 records; 49 human-reviewed Pidgin)
                          |
                          v
QLoRA fine-tuning of Qwen2.5-1.5B-Instruct
                          |
                          v
GGUF Q4_K_M (~941 MB) -> llama.cpp
```

The rules engine is the source of numerical truth for training data and verification. It is **not** invoked at inference time: the submitted GGUF is evaluated independently by the challenge infrastructure.

## Design decisions

- **Raw model only.** The evaluation measures the GGUF directly; an app layer would add nothing to the score.
- **1.5B over 0.6B.** Accuracy dominates once throughput clears the profiler's fixed 15 t/s reference. A 0.6B model was 2.1x faster locally but unreliable on statutory facts.
- **Q4_K_M over Q5/Q8.** ~1.7 GB peak RSS against a 7 GB budget, with no observed accuracy regression on domain evaluations.
- **Three dataset revisions** (v5 → v6b → v6c), each driven by held-out evaluation failures. v6c removed canned preambles so answers start directly with the computation.
- **Decimal everywhere.** Monetary values are Python `Decimal`, serialized as strings; every calculation and counterfactual record is verified against the engine before training.

## Verified facts

Every legal fact traces to `sources/SOURCE_REGISTER.md` (F-001…F-007), verified against the Nigeria Tax Act 2025 and, for NHF, the NHF Act 1992 as amended by the BFA 2022.

## Measured results

| Metric | Value |
|---|---|
| Generation (local, i5-8250U locked 1.6 GHz, 4 threads) | 10.09 t/s |
| ADTC profiler participant run | 8.83 t/s, 1,691 MB peak RSS, no throttling |
| Natural English evaluation | 8/8 total tax, 8/8 chargeable income |
| Clean held-out English (novel amounts/wording) | 3/12 exact, 7/12 within NGN 1, 12/12 chargeable income |
| Pidgin holdout | 2/3 total tax, 3/3 chargeable income |

## Known limitations

- Exact band totals can drift on novel amounts, especially band-boundary segmentation above NGN 25M.
- Scoped to single-turn Q&A; multi-turn dialogue is not supported.
- Full technical writeup and benchmark details: `REPORT.md`.

## Reproducibility

Base model: `Qwen/Qwen2.5-1.5B-Instruct` (Apache 2.0). QLoRA via Unsloth on a Colab T4 (rank 32, alpha 64, 3 epochs, lr 2e-4). Dataset generation, verification, and training scripts live in `scripts/`; commands in `README.md`.
