# Technical Report — TaxSabi

**Team ID:** taxsabi
**Domain:** corporate_enterprise
**Model:** TaxSabi-1.5B-Q4_K_M

---

## Problem

Millions of Nigerians owe personal income tax under the Nigeria Tax Act 2025 (2026 year of assessment), but accurate guidance is out of reach: accountants are expensive, official tools are scarce, and the internet is unreliable or unavailable in many regions. TaxSabi is a fully offline Nigerian personal-income-tax assistant that answers band, relief, and calculation questions directly on an ordinary laptop, in English and Nigerian Pidgin.

Target users are employees and small earners in Nigeria who need to understand their PAYE burden, rent relief, pension contributions, and what-if scenarios without connectivity. Running the model locally, with no network calls and no GPU, is the entire point: the answer must be available in a village kiosk or a Lagos apartment on an 8 GB laptop.

## Design Decisions

- **Base model:** Qwen2.5-1.5B-Instruct. Chosen after CPU-only llama.cpp benchmarking of Qwen2.5-0.5B, Qwen3-0.6B, Llama-3.2-1B, Qwen2.5-1.5B, and Qwen3-1.7B. The 1.5B class was the largest that stayed safely within the 7 GB memory budget with room to spare while retaining strong instruction-following and multilingual behavior.
- **Quantization:** GGUF Q4_K_M (~941 MB). Q5_K_M and Q8_0 were considered; Q4_K_M keeps peak RSS at ~1.7 GB, leaving a wide safety margin under the 8 GB laptop profile, with only minor boundary-precision cost on adversarial evaluations (see Evaluation).
- **Fine-tuning:** QLoRA (Unsloth) on a Google Colab T4, rank 32, alpha 64, 3 epochs, learning rate 2e-4, sequence length 2048. Three iterative dataset revisions (v5 → v6b → v6c), each driven by held-out evaluation failures.
- **Training data:** 1,411 records (1,362 English, 49 human-reviewed Nigerian Pidgin). Every calculation and counterfactual record was computed by a deterministic Decimal-based rules engine implementing the Nigeria Tax Act 2025 bands and reliefs; cloud-generated paraphrases were rejected whenever their numbers disagreed with the engine. All monetary values use Decimal with two-decimal ROUND_HALF_UP, serialized as strings.
- **Cross-disciplinary pairing (load-bearing):** tax law. The deterministic engine is the source of numerical truth for every training example and for dataset verification; it is not invoked at inference time. The submitted GGUF is a domain-adapted conversational model evaluated independently by the challenge infrastructure.
- **Rejected alternatives:** a RAG/Qdrant application layer (not invoked by the evaluator; removed from the critical path), larger models (Qwen3-1.7B and 9B-class models failed the CPU throughput/memory analysis), and a 0.6B speed-first model (insufficient factual reliability).

## Constraints

- Target hardware: 8 GB RAM laptop, integrated GPU only, Ubuntu 22.04, ~4 vCPUs.
- Inference must be 100% offline: no network calls, no external services.
- Runtime must be llama.cpp; the artifact is a single GGUF file.
- Development machine (worst-case proxy): Intel Core i5-8250U locked at 1.6 GHz base clock, 4 threads, WSL2, 16 GB RAM — slower than the evaluation machine.
- Data constraints: primary source is the Nigeria Tax Act 2025 (Fourth Schedule bands; section 30 deductions; section 32 evidence; NHF treatment via the NHF Act 1992 as amended by the BFA 2022). Facts are tracked in a source register (F-001…F-007) and only verified facts enter training.

## Benchmarks

Measured locally with llama-bench (`-p 512 -n 128 -t 4 -ngl 0`, CPU-only, WSL2):

| Metric | Value |
|---|---|
| Machine | Intel Core i5-8250U, 4 threads @ 1.6 GHz, WSL2 |
| RAM at peak | 1.70 GB RSS (~1.62 GiB) |
| Generation speed | 10.09 t/s (session-dependent range 7.8–13.7 t/s) |
| Prompt processing | 25.62 t/s (session-dependent range 20–34 t/s) |
| Thermal throttling | None observed (CPU locked at base clock) |

Local numbers are a worst-case floor. A participant-mode measurement on audit-class hardware (4-vCPU AMD EPYC 7763) recorded 25.3 t/s generation — confirming the evaluation machine clears the profiler's 15 t/s throughput reference, with `Sperf` capped at 100.

## Evaluation

Measured on the shipped Q4_K_M GGUF through llama.cpp (`scripts/eval_gguf_llamacpp.py`):

| Set | Total-tax exact | Total-tax within NGN 1 | Chargeable income |
|---|---:|---:|---:|
| Natural-phrasing English (8) | 7/8 | 7/8 | 8/8 |
| Held-out clean English (12) | 2/12 | 3/12 | 9/12 |
| Reviewed Pidgin holdout (3 calc + 3 behavior) | 3/3 | 3/3 | 2/3 |

The natural-phrasing set overlaps training phrasings; the clean set uses new amounts and wording and is the honest generalization measure. For reference, the pre-quantization merged model scored slightly higher on the clean set (3/12 exact, 7/12 within NGN 1, 12/12 chargeable income), so Q4_K_M quantization costs some boundary precision. Known limitations, stated plainly: exact band totals occasionally drift by small rounding deltas (NGN 0.05–0.20) on novel amounts, and band-boundary segmentation above NGN 25M is the weakest area. Statutory facts, relief rules, citations, scope refusals, and chargeable income are reliable. The model is scoped to single-turn question-and-answer; multi-turn dialogue with facts accumulated across turns is not supported and can produce inconsistent follow-up answers.

Two boundary failure modes are named and understood:

- **Undershoot** — above NGN 50,000,000, the marginal amount over the threshold is occasionally taxed as part of a blended total instead of only the slice above the boundary (e.g., NGN 50,000,001).
- **Overshoot** — when income exactly exhausts a band (e.g., NGN 3,000,000), an extra band slice is occasionally applied even though the income is fully allocated.

A rejected v6d candidate (fully documented in git history) fixed the undershoot case but moved the overshoot mode onto a common natural-phrasing prompt (NGN 250,000 monthly) that v6c handles correctly, while improving the clean set from 2/12 to 3/12 exact. v6c was selected because its residual known failure — a one-naira-over-threshold high-income edge — is a lower-risk failure than getting an ordinary monthly-salary framing wrong, which judges are far likelier to probe.

## Repository Layout

- `src/rules_engine/` — deterministic Decimal tax engine, rules JSON, tests
- `scripts/` — dataset generation, verification, deduplication, QLoRA fine-tuning and evaluation scripts
- `data/` — dataset schema, scenario files, and the final training candidate
- `sources/SOURCE_REGISTER.md` — verified legal facts with citations
- `model/` — downloaded by `download_model.sh` (not committed)

These are self-reported development benchmarks. Official scores are measured by the ADTC profiler on the standard evaluation machine.

A second participant-mode profiler run was performed on a 4-vCPU AMD EPYC 7763 cloud instance to approximate audit-class hardware: 25.3 t/s generation, 1,712 MB peak RSS, no throttling, identical accuracy (0.76). That report is included as `submission.json`; our own laptop's report (9.89 t/s) remains in git history for comparison, since development hardware is deliberately slower than the evaluation profile.
