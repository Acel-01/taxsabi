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
Nigeria Tax Act 2025 + NTAA 2025 + PenCom VPC Guidelines
(extracted text + verified source register, ~695K chars)
                          |
                          v
Deterministic Decimal tax rules engine (src/rules_engine/)
                          |
                          v
Engine-verified datasets: SFT v2 (1,929 examples),
KTO v1 (3,144 labels), GRPO pools (1,284 prompts)
                          |
                          v
QLoRA pipeline: DAPT v5 -> SFT v2 -> KTO v1 -> GRPO v2
(Unsloth, A100 40GB, no thinking mode)
                          |
                          v
GGUF Q8_0 (1.70 GiB) -> llama.cpp
```

The rules engine is the source of numerical truth for training data and verification. It is **not** invoked at inference time: the submitted GGUF is evaluated independently by the challenge infrastructure.

## Design decisions

- **Qwen3-1.7B over smaller models.** Benchmarked against Qwen2.5-0.5B, Qwen3-0.6B, Llama-3.2-1B and the Gate-1 Qwen2.5-1.5B; the 1.7B class is the largest that stays inside the 8 GB / 4 vCPU profile while holding statutory facts and Pidgin.
- **Q8_0 over Q4/Q5/Q6.** A measured fidelity study (held-out × dev × band-phrasing tests) showed Q4_K_M and Q6_K corrupt the 2026 band table and Q4 flips arithmetic; Q5_K_M substitutes an older band table. Q8_0 reproduces the full-precision model, so we accepted ~30–45% lower throughput and 1.70 GiB for accuracy. Details: `provenance/merge_quantize.md`.
- **Four-stage pipeline.** DAPT absorbs the statutes and procedures; SFT shapes working-first answers and conversation behavior; KTO teaches citation/answer preferences from deterministic labels; GRPO optimizes the exact final tax figure with the engine as verifier. GRPO v2 is frozen after v3 traded behavior for no calculation gain.
- **Raw model only.** The evaluation measures the GGUF directly; an app layer would add nothing to the score.
- **Decimal everywhere.** Monetary values are Python `Decimal`, serialized as strings; every calculation and counterfactual record is verified against the engine before training.

## Verified facts

Every legal fact traces to `sources/SOURCE_REGISTER.md` (F-001…F-019), verified against the Nigeria Tax Act 2025, the Nigeria Tax Administration Act 2025, and the Pension Reform Act 2014 / PenCom VPC Guidelines.

## Measured results

| Metric | Value |
|---|---|
| Participant profiler (shipped Q8_0, i5-8250U, 4 threads) | 3.3–4.7 t/s generation, ~1.94 GB peak RSS, `Sperf` 22–31, `Seff` ~73, no throttling |
| Held-out probe, novel amounts (10 calculations) | 5/10 exact final tax, 7/10 chargeable income |
| Dev probe (9 calculations) | 8/9 exact final tax |
| Paraphrase suite (40 calculations) | 17/40 exact, 5/8 phrasing groups consistent |
| Citation discipline | zero out-of-register sections across 1,010 captures |

## Known limitations

- Band-list answers are phrasing-sensitive: 2 of 6 tested phrasings fail even at full precision (quantization preserves, not causes, this).
- The clarify/no-clarify boundary is occasionally wrong on ambiguous Pidgin amounts.
- A few statutory nuances remain imperfect (student filing duty, “CRA” abbreviation, NIRS naming).
- Scoped to single-turn Q&A; long multi-turn fact accumulation is not supported.
- Full technical writeup, provenance disclosure and before/after examples: `REPORT.md`.

## Reproducibility

Base model: `unsloth/Qwen3-1.7B` at revision `6262b50d6c1f8ee5e4ac750d710c33603bfc2a0c` (Apache 2.0). QLoRA via Unsloth (rank 64, alpha 128; DAPT rank 128). Training scripts, run metadata, per-step GRPO metrics and checksums live in `provenance/`; dataset details in `provenance/dataset_info.md`; merge/quantization commands in `provenance/merge_quantize.md`.
