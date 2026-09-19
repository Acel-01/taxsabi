# Stage Gates — TaxSabi Training Pipeline

What each training stage must demonstrate before the next stage begins, how each metric is measured, and which eval file to use. Gates are deliberately strict on §1–§4 behaviors (accuracy, citations, clarification, scope) and looser on style.

## Metric definitions

| Metric | Definition | Measured with |
|---|---|---|
| `calc_exact` | labelled annual tax exactly equals engine ground truth | `data/eval/probe_prompts_heldout.jsonl`, `baseline_prompts.jsonl`, `paraphrase_suite.jsonl`, `coach_eval.jsonl` via `eval_gguf_llamacpp.py` or `compare_captures.py` |
| `calc_tol` | labelled annual tax within NGN 1 of ground truth | same |
| `ci_exact` | labelled chargeable income equals ground truth | same |
| `savings_exact` | stated tax saving equals ground truth | counterfactual records |
| `para_groups` | paraphrase groups (of 8 calc cores) where all five phrasings yield the same predicted tax | `compare_captures.py` paraphrase section over `paraphrase_suite.jsonl` |
| `mt_turns` | multi-turn scorable turns answered exactly | `run_multiturn.py` + `compare_captures.py` over `multiturn_suite.jsonl` |
| `retention` | `mt-10` (accumulated facts) final turn exact, and no corrective re-asks in `mt-02` | same |
| `judge_fact` | mean judge score for accuracy/citation/scope dimensions | `judge_responses.py` over probe + coach captures |
| `judge_coach` | mean coach dimension score (constitution §5) | `judge_responses.py` over `coach_eval.jsonl` captures |
| `undesirable` | share of judged responses marked undesirable (any §1–§4 violation) | same |
| `invented` | numbers of invented citations, reliefs, or thresholds observed in manual sample of 30 outputs | manual review of captures |
| `speed` | generation tokens/sec in the participant profiler | `adtc-profiler` on the exact shipped GGUF |
| `size` | GGUF file size | `ls -l model/*.gguf` |

Naming: a gate like `calc_exact ≥ 80%` is evaluated on the held-out probe unless stated otherwise.

## Gate table

| Stage | Hard gate (must pass) | Targets | Regression guards |
|---|---|---|---|
| **Base (Qwen3-1.7B)** | none — reference capture only | record all baselines | n/a |
| **1. DAPT carry** | no behavioral collapse: model still produces tax-shaped answers on the probe; `para_groups` not below base | factual recall of bands/deductions appearing in outputs | `calc_exact` not below base−5pp; run `scripts/build_heldout_probe.py --verify-only` before data assembly |
| **2. SFT** | `calc_exact ≥ 80%`; `ci_exact ≥ 80%`; `undesirable ≤ 10%`; `invented = 0` in sample | `para_groups ≥ 6/8`; `mt_turns ≥ 70%`; `judge_fact ≥ 4.0`; Pidgin suite no worse than v6c baseline | no regression on `paraphrase_suite` vs base; language consistency 8.1 |
| **3. KTO** | KTO must not drop `calc_exact` by more than 2pp vs SFT | `judge_coach ≥ 4.2`; `undesirable ≤ 5%`; improved clarification behavior (mt-04) | run same captures through both checkpoints; inspect 20 changed answers |
| **4. GRPO** | `calc_exact ≥ 90%`; `calc_tol ≥ 95%` | reward-shaping principles hold: no fabricated figures, citation format stable | `speed` within 10% of SFT; no drop in `judge_coach` |
| **Final GGUF** | profiler run completes on the exact shipped file; all evals run on the GGUF, not the merged fp16; sha256 in `CHECKSUMS.txt` | `speed` maximized without violating accuracy gates; before/after report generated | `size` within contest budget (≤ 8 GB, target ≤ 2 GB); provenance bundle complete (Gate 2 requirement) |

## Running the full gate evaluation for a stage

```bash
# 0. guardrail - no training/runtime overlap
uv run python scripts/build_heldout_probe.py --verify-only
uv run python scripts/build_paraphrase_suite.py --verify-only
uv run python scripts/build_multiturn_suite.py --verify-only
uv run python scripts/build_coach_eval.py --verify-only

# 1. capture: single-turn (probe, paraphrase, coach), then multi-turn
uv run python scripts/run_baseline.py --model model/<stage>.gguf \
  --prompts data/eval/probe_prompts_heldout.jsonl \
  --out data/captures/<stage>_heldout.jsonl --label <stage>
uv run python scripts/run_baseline.py --model model/<stage>.gguf \
  --prompts data/eval/paraphrase_suite.jsonl \
  --out data/captures/<stage>_paraphrase.jsonl --label <stage>
uv run python scripts/run_baseline.py --model model/<stage>.gguf \
  --prompts data/eval/coach_eval.jsonl \
  --out data/captures/<stage>_coach.jsonl --label <stage>
uv run python scripts/run_multiturn.py --model model/<stage>.gguf \
  --suite data/eval/multiturn_suite.jsonl \
  --out data/captures/<stage>_multiturn.jsonl --label <stage>

# 2. score and compare against the previous stage
uv run python scripts/compare_captures.py \
  --before data/captures/<prev>_heldout.jsonl \
  --after  data/captures/<stage>_heldout.jsonl \
  --out reports/<prev>_vs_<stage>_heldout.md

# 3. judge the coach and probe captures
uv run python scripts/judge_responses.py \
  --captures data/captures/<stage>_coach.jsonl \
  --out data/captures/<stage>_coach_judged.jsonl \
  --endpoint http://127.0.0.1:8081/v1 --model <judge>

# 4. speed and size on the shipped artifact
python3 -m adtc_profiler ...
```

## Tie-in to competition scoring

The Round-1 formula was `Stotal = 0.50·Sacc + 0.30·Sperf + 0.20·Seff − Pthermal + bonus (≤10)`.

- `Sacc` (50%) is what the gates above maximize: arithmetic correctness, factual accuracy, and the judge-scored behaviors.
- `Sperf` (30%) is generation throughput `min(t/s ÷ 15, 1) × 100`. Every stage capture should record t/s alongside quality so speed regressions are caught at the checkpoint that causes them.
- `Seff` (20%) is the profiler efficiency score — check it on the final artifact, not intermediate checkpoints.
- Bonus points historically came from completeness of the submission (provenance, before/after evidence, documentation), which is why every stage keeps captures and reports in `data/captures/` and `reports/`.

## Failure protocol

If a gate fails: do not proceed. Compare the failing dimension against the previous stage capture, inspect at least 20 changed answers manually, categorize the failures (arithmetic, format, citation, language, scope), and fix the *data or reward*, not the eval. Re-run the guardrails after any training-data change.
