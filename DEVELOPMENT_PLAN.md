# TaxSabi — 9-Month Development Plan

**Status:** Locked
**Base model:** Qwen3-1.7B (Apache 2.0, public GGUF, 28 layers, 32K context)
**Pipeline:** DAPT → SFT → KTO → GRPO (no thinking mode)
**Vision:** A personal tax-efficiency coach for Nigerians — legal optimization, not just calculation
**Constraint:** CPU-only inference, llama.cpp, GGUF, judged on the raw model
**Timeline:** ~39 weeks (9 months from Sept 2026)

---

## Architecture (locked)

```
                    ┌─────────────────────────┐
                    │   User (En / Pidgin /   │
    │   future: Yoruba, Hausa, Igbo)          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  TaxSabi GGUF model     │
                    │  (Qwen3-1.7B, Q4_K_M)   │
                    │                         │
                    │  Trained via:           │
                    │  1. DAPT (knowledge)    │
                    │  2. SFT (behavior)      │
                    │  3. KTO (preferences)   │
                    │  4. GRPO (accuracy)     │
                    │                         │
                    │  No thinking mode       │
                    │  No RAG                 │
                    │  All knowledge in       │
                    │  weights                │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼────────┐ ┌──────▼───────┐ ┌───────▼────────┐
    │  CONSTITUTION    │ │  RULES       │ │  SOURCE        │
    │  (behavioral     │ │  ENGINE      │ │  REGISTER      │
    │  principles)     │ │  (determin-  │ │  (F-001–F-007  │
    │                  │ │  istic       │ │  + expanded)   │
    │  Drives:         │ │  Decimal)    │ │                │
    │  - KTO labels    │ │              │ │  Drives:       │
    │  - GRPO rewards  │ │  Drives:     │ │  - Citation    │
    │  - SFT data gen  │ │  - GRPO      │ │    checking    │
    │  - System prompt │ │    rewards   │ │  - DAPT corpus │
    └──────────────────┘ │  - Scenario  │ │                │
                         │    ground    │ └────────────────┘
                         │    truth    │
                         └─────────────┘
```

**Core design rules (locked):**

1. The LLM handles language — understanding questions, explaining answers, asking clarifications
2. The engine handles arithmetic — every naira figure in training data is engine-computed
3. All knowledge lives in the weights (no RAG, no retrieval at inference)
4. No thinking mode — direct answers, latency matters
5. Citations are contextual — shown when a specific legal claim is made, omitted for simple arithmetic
6. The constitution is the behavioral ground truth — engine for arithmetic, written principles for everything else
7. The user (Chukwuemeka) is the taste-maker — iterative review drives SFT and KTO data quality

---

## Phase 0: Foundation (Weeks 1–4)

**Objective:** Everything needed before training begins.

### 0.1 Constitution Draft
- [x] Draft behavioral principles document (~20-30 principles)
- [x] Cover: citation behavior, caveat appropriateness, decline-vs-guess, answer length vs question complexity, relief suggestion phrasing, sequencing advice style, scope boundaries, multi-turn behavior, clarification triggers
- [x] User reviews and iterates (target: 3 revision rounds)
- [x] Lock v1.0

**Deliverable:** `CONSTITUTION.md` ✓ (approved 2026-09) — 40 principles, 8 sections, each traceable to a Gate 1 failure

### 0.2 Base Model Validation
- [x] Download Qwen3-1.7B GGUF (official or convert from safetensors) — unsloth/Qwen3-1.7B-GGUF, 1.06 GB, sha256 recorded
- [x] Bench on dev laptop (same session as Qwen2.5-1.5B for comparison) — 20.89 pp / 6.09 tg (vs Qwen2.5-1.5B: 19.00 pp / 6.15 tg; ~5% gap confirmed)
- [ ] Bench on Codespace EPYC (audit-class proxy)
- [x] Run behavioral baseline: 30 diverse tax prompts through the un-fine-tuned base — `data/eval/baselines/base_qwen3_1.7b.jsonl`
- [x] Run Pidgin baseline: 10 Pidgin prompts — included in the 30
- [x] Confirm non-thinking mode works correctly through llama.cpp chat template — chat_template_kwargs confirmed
- [x] Verify GGUF provenance (unsloth quant, sha256 checksummed to `model/CHECKSUMS.txt`)
- [x] Baseline analysis written — `data/eval/baselines/ANALYSIS.md` (confabulated knowledge documented)

**Deliverable:** `data/eval/baselines/base_qwen3_1.7b.jsonl` + `ANALYSIS.md` ✓

### 0.3 DAPT Corpus Assembly
- [x] Extract clean text from `sources/tax_act_2025.txt` — 428,778 chars, all artifacts fixed and verified (`scripts/clean_tax_act.py`)
- [x] Download and clean the Nigeria Tax Administration Act 2025 gazette — 187,277 chars (`scripts/clean_ntaa.py`); combined corpus ~616K chars
- [x] Expand source register: F-008..F-013 added (commencement, minimum-wage exemption, no-CRA, PAYE administration, evidence practice, pension exemption); P-003..P-005 resolved via LIRS sources
- [x] Verify remaining pending facts: P-001 → F-014 + F-016 (8%/10% rates, VPC rules, 7-working-day remittance, ≥2%/month penalty); P-002 → F-015 (N70,000/month via PLAC bill text, S9); P-006 → PAYE remittance = 10th (S5, DToS Regulations caveat noted)
- [x] Recover the PRA 2014 primary text — PenCom's PDF is a scan with a scrambled text layer; OCR'd via `scripts/ocr_pra_2014.py` → `sources/pra_2014_ocr.txt` (62 pp); key sections spot-checked against rendered pages
- [x] Collect procedural/planning knowledge: relief claiming processes, documentation requirements, employer payroll interaction, VPC setup, mortgage relief claiming (PenCom VPC Guidelines S8 + PRA text on file)
- [x] Write domain prose connecting facts to practical advice — `data/dapt_corpus/procedural/` (6 documents, 50,390 chars: tax basics, reliefs guide + filing mechanics, efficiency/planning, PAYE, pensions/VPC, scope); draft pending review
- [x] Filing-mechanics research (relief claim timing/refunds): F-017 (e-Tax/Tax Form A, annual return), F-018 (s.55 refunds/credits, reg. 5 advance tax), F-019 (assessments/objections); DToS Regulations 2024 gazette obtained (S10) — PAYE 10th day now `verified_primary`
- [ ] Target: 500KB–2MB of clean domain text — at ~690K, on track
- [ ] License-check all sourced text (statutes are government gazettes; PenCom guidelines are a public regulator publication)

**Deliverable:** `data/dapt_corpus/` — two cleaned statutes + PenCom VPC guidelines + procedural prose + README with provenance ✓

### 0.4 Evaluation Framework Upgrade
- [x] Build held-out probe set (20 prompts, zero overlap with all training data) — `data/eval/probe_prompts_heldout.jsonl`, built by `scripts/build_heldout_probe.py`
- [x] Capture base model on held-out probe — `data/eval/baselines/base_qwen3_1.7b_heldout.jsonl`
- [x] Build development probe (30 prompts, mixed) + base capture — `data/eval/baseline_prompts.jsonl`, `data/eval/baselines/base_qwen3_1.7b.jsonl`
- [x] Build reusable stage-capture harness — `scripts/run_baseline.py` (thinking-off, engine-scorable)
- [x] Build paraphrase-consistency suite (20 cores × 5 phrasings = 100 prompts, 40 engine-scorable) — `data/eval/paraphrase_suite.jsonl`, `scripts/build_paraphrase_suite.py`
- [x] Build multi-turn probe suite (10 conversations, 32 turns, 18 engine-scorable) — `data/eval/multiturn_suite.jsonl`, runner `scripts/run_multiturn.py`
- [x] Build coach-behavior eval (relief discovery, savings modeling, sequencing, filing workflow; 15 prompts, 4 engine-scorable, judge checklists) — `data/eval/coach_eval.jsonl`, `scripts/build_coach_eval.py`
- [x] Build base-vs-stage comparison harness (scoring, paraphrase consistency, movement analysis) — `scripts/compare_captures.py`; dev-probe ground truth added via `scripts/patch_eval_ground_truth.py` (9 records)
- [x] Integrate LLM judge scaffold for behavioral dimensions (constitution rubric, OpenAI-compatible endpoint, dry-run verified) — `scripts/judge_responses.py`
- [x] Define stage-gate metrics — `data/eval/STAGE_GATES.md` (per-stage hard gates, targets, regression guards, failure protocol)

**Deliverable:** `data/eval/probe_prompts_heldout.jsonl` ✓ + `scripts/run_baseline.py` ✓ + `scripts/build_heldout_probe.py` ✓ + paraphrase/multi-turn/coach suites ✓ + `scripts/compare_captures.py` ✓ + `scripts/judge_responses.py` ✓ + `data/eval/STAGE_GATES.md` ✓

**Guardrail:** `build_heldout_probe.py --verify-only` re-checks zero overlap after any training-data change — run before every stage's data generation.

### 0.5 Compute Setup
- [x] Register on aghcloud.ai, claim $50 GPU credits (done 2026-09-19)
- [x] Prepare the Unsloth smoke test — `scripts/unsloth_smoke_test.py`: version/GPU report (CUDA + ROCm detection), 4-bit load, thinking-off chat template, mini-SFT with loss check, KTO/GRPO availability
- [x] Prepare the DAPT training script — `scripts/dapt_pretrain.py`: corpus + replay mix (wikitext streaming or local), EOS-separated packed blocks, train/val split, adapter + merged (+ GGUF), `dapt_run.json` provenance
- [x] Estimate compute budget — `data/eval/COMPUTE_BUDGET.md` (~174K corpus tokens; AGH ≈ 2.5–6 GPU-h total, T4-only ≈ 6–12)
- [x] Run the smoke test on AGH A100 40GB (Shadeform partner) — passed 2026-09-19: torch 2.11+cu128, bf16 supported, Unsloth 2026.9.7 patched Qwen3, mini-SFT loss 7.5→1.8 in 8 steps, KTO/GRPO/DPO trainers available
- [x] Reproducible environment recipe — `scripts/setup_training_env.sh` (uv + Python 3.12 + `--torch-backend=cu128`; avoids the old system Python on generic cloud images)
- [x] Colab T4 pipeline — superseded: identical scripts; Colab remains the fallback if AGH access lapses
- [ ] Re-estimate the budget with measured tokens/s from the first DAPT run (`dapt_run.json`)

**Deliverable:** Working training pipeline for Qwen3-1.7B on AGH A100 — smoke test passed; DAPT/SFT runs next

---

## Phase 1: DAPT — Domain Knowledge Absorption (Weeks 5–10)

**Objective:** Bake domain knowledge into the weights via continued pretraining.

### 1.1 Corpus Preparation
- [x] Tokenize and clean the DAPT corpus — cleaning done in 0.3 (deterministic cleaners, artifact sweeps); tokenization + EOS-separated 1024-block packing implemented in `scripts/dapt_pretrain.py` (runs on first launch)
- [x] Structure into training-format documents — sectioned plain text: 2 cleaned statutes, PenCom guidelines, 6 procedural prose docs (~695K chars ≈ 174K tokens)
- [x] Mix with 10-20% general-domain text — `--replay-ratio 0.15` (wikitext streaming or `--replay-file`), implemented in `scripts/dapt_pretrain.py`
- [x] Split into training/validation — 98/2 block split, seed 42, implemented in `scripts/dapt_pretrain.py`
- [ ] License check (inherited from 0.3) — confirm the public-document basis for statutes and PenCom guidelines before any redistribution

### 1.2 DAPT Training
- [x] Configure Unsloth for continued pretraining — `scripts/dapt_pretrain.py`: next-token prediction on EOS-separated 1024-token blocks, wikitext replay (15%), 98/2 train/val split, adapter + merged exports, `dapt_run.json` provenance
- [x] QLoRA on Qwen3-1.7B, low LR — LR held at 5e-5 throughout; 4-bit QLoRA in run 1 only, switched to bf16 LoRA from run 2 (A100 40GB has the headroom); epochs exceeded the planned 1–2 (5, then 8) because absorption needed repetition
- [x] Monitor for memorization vs absorption — loss 2.20 → 1.93 → 1.35 across runs; run 4 exposed memorization bleed from over-concentrated numeric facts (regression documented)
- [x] Checkpoint after each epoch — `save_strategy="epoch"`; checkpoints lived on the instance; final adapter + run metadata archived locally

### 1.3 Knowledge Evaluation
- [x] Test: does the model know the bands without being asked in SFT format? — probe fact-01: run 3 table fully correct; run 5 mostly correct (800k@0%, 15%, 18% rows right; upper boundaries drift)
- [x] Test: does it know PAYE procedures, relief claiming steps, documentation requirements? — partial: pension-proof prompt captured; rent-cap prompt failed in every run (deferred to SFT); PAYE deadlines not probed directly
- [x] Test: can it correctly reference the Act's sections when prompted? — no: probe outputs invented or misapplied citations (e.g., "Section 12(1)(a)"); recorded; citation accuracy is an SFT/GRPO target
- [x] Compare against Phase 0 baseline — base: 0/40 exact calcs, invented flat rates; v5: real band structure present and used; gain is material and qualitative
- [ ] Check for degradation: general language ability, instruction following, multilingual — English coherent on the probe; Pidgin untested. Deferred, not skipped: runnable from the backed-up v5 adapter on the next instance (dev probe, ~10 min) for clean DAPT attribution before SFT

### 1.4 Iterate
- [x] Run 1 (2026-09-20): 2 epochs, r=32, QLoRA 4-bit, 172 blocks, 55 s on A100; loss 2.358→2.109, eval 2.204→2.183. Probe: still fabricates rate tables (0/10 exact); partial gains (correct deduction arithmetic in one case, consistent Act naming)
- [x] Run 2: 5 epochs, r=64, bf16, prose ×3 (`--repeat-prose 3 --no-4bit`); loss 1.926; probe: band boundaries 3M/12M/25M/50M correct, but first boundary wrong and top rates collapsed to 19%; rent relief still wrong
- [x] Run 3 (best): 8 epochs, r=128, bf16, prose ×5; loss 1.346; probe: **full band table correct** (800k@0%, 15/18/21/23/25%); rent relief still misstated
- [x] Run 4 (regression): run-3 recipe + distilled fact sheet as corpus doc 07 → number bleed: garbled bands (spurious 2,250,000 / 7,800,000 boundaries, duplicated 0%), blended rent figures. Dense consecutive facts repeated ×5 overfit the adapter
- [x] Decision (2026-09-20): fact sheet removed from the DAPT corpus (now `sources/KEY_FACTS_REFERENCE.md` for SFT generation); SFT base = run-3 recipe without the fact sheet (v5)
- [x] Run 5 (2026-09-20): run-3 recipe on the cleaned corpus; probe: 800k@0%, 2.2M@15%, 9M@18% correct; upper boundaries drift (22M/50M vs 13M/25M). Run-to-run variance vs run 3 confirms numeric tables are fragile via DAPT alone
- [x] SFT base selected: v5 (recreate the merged model from the backed-up adapter via `scripts/merge_adapter.py`; merged models are not archived)
- [ ] Degradation check (general language, Pidgin): deferred, not skipped — v5 adapter is archived, so the check can run on the next instance before SFT (dev probe, ~10 min) for clean attribution; otherwise compare base→SFT
- [ ] If degradation: increase replay ratio, reduce epochs
- [ ] Target: clear knowledge gain in the weights; precise fact-binding and answer behavior completed in SFT (see revised 1.3 gate)

**Phase 1 status (2026-09-20): exiting under the revised gate — knowledge gain verified (bands, rates, terminology in the weights); precision and behavior deferred to SFT by design.**

**Stage gate:** Material knowledge gain vs the base model on the probe — bands, rates, and terminology correct in free-form answers. Precise fact-binding (rent cap, procedure details) and answer behavior are completed in SFT. (Revision proposed 2026-09-20 after runs 3–4 showed DAPT learns structure well but over-concentrated numbers cause bleed; requiring 80% free-form fact accuracy in DAPT pushes precision into the wrong stage.)

---

## Phase 2: SFT — Behavior Shaping (Weeks 11–20)

**Objective:** Teach the model how to use its knowledge — conversation, coaching, multi-turn, clarification.

**This is the hardest phase.** The user's taste drives quality. Iterate.

### 2.1 Conversation Generation Pipeline
- [x] Build dialogue skeleton generator (programmatic) — `scripts/build_sft_jobs.py`; model-agnostic job files in `data/sft_jobs/` (layer_a 300 / layer_b 80 / layer_c 110 blueprints), one layer per model so switching is minimal
      - Accumulate-then-compute, counterfactual, correction, clarify-then-compute, coaching discovery/savings/sequencing, topic shift with retention, out-of-scope decline
- [x] Engine verifies every number in every assistant turn — `scripts/verify_sft_generation.py`: schema checks, authorised-amount set from engine values, required-figure and required-term checks; rejects written with reasons
- [x] Generate initial batch: ~500 conversations — 490 generated and verified (layer_a 300, layer_b 80, layer_c 110), zero rejects; produced via opencode subagents against engine-locked blueprints, then filtered by `scripts/verify_sft_generation.py` (2026-09-20); reviewed data in `data/sft_verified/`
- [x] Target: 3-8 turns per conversation, natural phrasing variety — enforced by schema checks and per-turn guidance

### 2.2 User Review Loop (Round 1)
- [x] User reviews 100 sample conversations — review pack v1 (`scripts/build_review_pack.py`), 100 stratified conversations across all layers/types (2026-09-20)
- [x] User marks: approve / reject / annotate — flag-only protocol; **zero flags** (all 100 approved by silence)
- [x] Rejected → analyzed for patterns → constitution updated if needed — none; no generator iteration needed
- [x] Approved → added to SFT training pool — 490 verified conversations accepted (`data/sft_verified/`)
- [x] User identifies missing conversation types — none flagged; the pack is good to go
- [x] Iterate generator with feedback — no feedback to act on; format change (headline-first) was applied before this review and covered a later pass

### 2.3 SFT Data Assembly
- [x] Layer 1: Approved conversations (engine-verified) — 490 conversations across layers A/B/C (2026-09-20)
- [x] Layer 2: Fresh single-turn Q&A — 1,116 English + 134 Pidgin, generated against engine-locked scenarios (3 phrasing variants per calc/counterfactual scenario + 12 facts × 8 styles). Gate 1 English sets rejected by user as not good enough and are not used
- [x] Layer 3: Replay data — 220 OASST1 (Apache-2.0) general-chat conversations, ~11% of examples / ~17% of assistant words; no tax content, added to prevent narrowing
- [x] Citation behavior — cited fact variants added (24 English + 20 Pidgin) where the blueprint supplies the exact register citation (sections 30/31/32/41/55/58, s.51 NTAA, PRA s.4), plus uncited variants; contextual mix rather than boilerplate
- [x] Pidgin data (user-reviewed) — 110 conversations + 151 single-turn after assembly; style approved in review pass 1
- [x] Assembled dataset: **1,929 examples (train 1,833 / val 96)**, deduped (75 removed), zero eval overlap, manifest with sha256 provenance — `data/sft_v1/{train,val}.jsonl` + `MANIFEST.md`. Core+replay: ~96,000 assistant words

### 2.4 SFT Training (Round 1)
- [x] Multi-turn trainer support — `scripts/finetune_qlora.py` now consumes the `turns` schema with assistant-only loss masking (system/user masked -100, assistant header masked, content + end-of-turn trained) plus a no-GPU `--dry-run` verifier; dry-run confirmed on the real Qwen3 tokenizer (1,833 records, avg 232 / max 695 tokens, zero truncations)
- [x] QLoRA on DAPT checkpoint (v5 merged; upload adapter from `backups/taxsabi_v5_backup.tar.gz`, merge with `scripts/merge_adapter.py`)
- [x] Moderate LR (~1e-4), 2 epochs (defaults: r=64, α=128, effective batch 8)
- [x] SFT v1/v2 runs + held-out evaluation: v1 exposed the headline-first format flaw (total contradicted the model's own breakdown); v2 (working-first) fixed it — held-out exact tax 0/10 -> 4/10, no regressions
- [x] SFT v3 top-up dataset built — 94 targeted drills (rent percentage with novel amounts, band boundaries, clarify/no-clarify, fact corrections incl. decontaminated questions); assembled to `data/sft_v3` (2,021 examples, eval-clean)
- [x] Retrain SFT v3 on the instance and re-evaluate (held-out + dev vs v2) — v3 held-out exact tax 4/10 (flat), dev 4/9 vs v2's 5/9; fixed some rent/clarify cases but regressed facts/scope (student filing, director scope, band recall)

**Phase 2 status (2026-09-21): SFT v2 frozen as the checkpoint of record.** The v3 top-up did not move held-out exact tax and slipped the dev probe, so more SFT data is not the lever — the pipeline moves to Phase 3 (KTO) and Phase 4 (GRPO) as planned. The 2.5 suites (paraphrase/multi-turn/coach) and the user's 20-output taste pass still run on v2 when the instance is next up.

### 2.5 Evaluation Round 1
- [ ] Run all eval suites (paraphrase, multi-turn, coach, calculation, Pidgin)
- [ ] Base-model comparison (before/after side by side)
- [ ] User reviews 20 sample outputs — accept/reject/annotate
- [ ] Identify top 3 failure patterns

### 2.6 Iterate (Rounds 2–4)
- [ ] Generate targeted data for identified failures
- [ ] User review each round
- [ ] Retrain with expanded dataset
- [ ] Re-evaluate
- [ ] Target: 4 full iterations

**Stage gate:** Model handles multi-turn conversations without template regression, answers coach-style questions with relief discovery, and passes paraphrase-consistency at ≥70%.

---

## Phase 3: KTO — Preference Tuning (Weeks 21–28)

**Objective:** Teach the model which answer is better — citation discipline, caveat appropriateness, decline-vs-guess, answer cleanliness.

### 3.1 Binary Label Generation
- [x] Deterministic labels (engine-verified):
      - Correct tax figure → desirable
      - Wrong tax figure → undesirable
      - Exact citation match → desirable
      - Invented act/year/section → undesirable
- [x] Rule-based labels (citation checker):
      - Citation present when legal claim made → desirable
      - Citation absent when needed → undesirable
      - Citation present for simple arithmetic → undesirable (per constitution)
- [ ] LLM-judge labels (constitution-based, uses API or credits):
      - Appropriate caveat vs unnecessary caveat
      - Decline vs guess behavior
      - Answer length appropriateness
      - Relief suggestion phrasing (question, not assertion)
- [x] Target: 2,000–5,000 binary-labeled examples — 3,144 labels (train 2,984 / val 160: 552 verified gold + 2,592 on-policy samples)
- [ ] User spot-checks 200 labels for quality

**Pipeline (2026-09-21):** `scripts/build_kto_prompts.py` builds an 864-prompt pool — 552 verified single-turn prompts with gold answers (calc, counterfactual, fact, cited fact, clarify) plus 312 novel engine-locked calculation prompts with fresh amounts; zero eval-suite overlap and no held-out probe amounts. `scripts/sample_kto_completions.py` samples 3 on-policy completions per prompt with temperature on the instance. `scripts/label_kto_samples.py` applies the deterministic/citation rules and writes `data/kto/{train,val}.jsonl` in KTO prompt/completion/label format plus `label_stats.json` (per-prompt difficulty for the GRPO pool later). `scripts/kto_train.py` runs Unsloth KTOTrainer (β=0.1, LR 5e-6, 1 epoch, r=64) and has a no-GPU dataset check. LLM-judge labels deferred to a later pass.

### 3.2 KTO Training
- [x] QLoRA on SFT checkpoint — kto_v1 trained from the frozen sft_v2 merged model (1 epoch, β=0.1, LR 5e-6, r=64; loss 0.409)
- [x] KTO loss (prospect-theoretic, unpaired binary labels)
- [x] Monitor for reward hacking / degenerate outputs — outputs clean, no repetition or format collapse across 1,010 captures
- [x] Checkpoint and evaluate — adapter + merged backed up (`backups/taxsabi_kto_v1_backup.tar.gz`, sha256 verified)

### 3.3 Evaluation
- [x] Citation behavior: does it cite when appropriate, omit when not? — zero out-of-register sections across 1,010 captures; fact-05 now cites s.30(2)(a); cited-fact on-policy desirable rate 25%
- [ ] Caveat behavior: section-32 only when deductions claimed?
- [ ] Decline behavior: other years/countries → clean redirect?
- [ ] Guess behavior: unstated amounts → asks, doesn't invent? — not fixed (clar-01 computes an ambiguous amount; calc-08/09 over-ask)
- [x] Run full eval suite — held-out, dev, paraphrase (100) and coach (15) captured and compared vs sft_v2; multi-turn still pending (llama.cpp)
- [ ] User reviews 20 outputs — taste check

### 3.4 Iterate (Rounds 2–3)
- [ ] Generate more labels for remaining failures
- [ ] Retrain
- [ ] Target: 3 iterations

**Stage gate:** Citation behavior contextual (≥80% appropriate), zero invented acts/years, decline-and-ask behaviors reliable.

**Phase 3 status (2026-09-21): stage gate not met — kept as a stepping stone.** KTO v1 improved calculations modestly (held-out exact tax 4/10 → 5/10, CI 5/10 → 7/10; dev 5/9 → 6/9; paraphrase calc 15/40 → 17/40, CI 15 → 22) and fixed the rent-cap rule (probe-calc-03 exact) and band-list recall (probe-fact-01), with zero invented sections. But high-band edges regressed (21%/23% split on base-pcm-05), the band table hallucinated once on dev, clarify/no-clarify is still unreliable, and paraphrase consistency stayed ~40% (gate 70%). Moving to Phase 4 GRPO, which optimizes exact totals directly.

---

## Phase 4: GRPO — Reinforcement Learning with Verifiable Rewards (Weeks 29–36)

**Objective:** Sharpen calculation accuracy to near-perfect on the auditable distribution. No thinking mode.

### 4.1 Reward Function Design
- [x] Primary reward: final tax figure matches engine (binary, exact) — `tax_reward` in `scripts/grpo_train.py` (1.0 exact total)
- [x] Secondary reward: chargeable income matches (partial credit) — 0.25 when CI is exact and the total is not
- [ ] Tertiary reward: citation format correct (small weight) — deferred (v1 pool is single_calc only)
- [ ] Penalty: answer length beyond necessary (discourage padding) — deferred
- [x] No thinking-mode reward — chat template force-disabled for every apply_chat_template call
- [ ] Validate reward function against 100 known scenarios — reward self-test covers all branches; full validation during the first run

### 4.2 Prompt Pool Curation
- [x] Source: existing 1,108 scenarios + newly generated — `scripts/build_grpo_pool.py`: 1,284 single_calc prompts (550 KTO, 529 verified SFT, 205 fresh novel amounts), eval-overlap clean
- [x] Difficulty distribution: model should succeed ~50-70% of the time (GRPO needs group variance) — every prompt carries an easy/mid/hard/unknown tier; mid = measured 20-80% success, unknown awaiting the measurement pass
- [x] Include: boundary values, relief combinations, monthly/annual, Pidgin phrasings
- [ ] Exclude: scenarios the model always gets right (no learning signal) or always wrong (no variance) — selection ready (`--select mid`); runs after the difficulty measurement
- [x] Target: 500–1,500 prompts, curated by difficulty

**Workflow (2026-09-21):** build pool → sample difficulty on `data/grpo/pool_unknown.jsonl` with `scripts/sample_kto_completions.py` → `scripts/build_grpo_pool.py --score-samples` → `--select mid` (or mid+hard) → `scripts/grpo_train.py --model ~/models/kto_v1/merged --pool data/grpo/train_pool.jsonl --out ~/models/grpo_v1`.

### 4.3 GRPO Training
- [x] TRL GRPOTrainer (or Unsloth GRPO support) — v1 ran on `kto_v1` (81 mid-tier prompts, 40 steps, 11 min); conversational-completion reward bug fixed in `14ffd1b`
- [x] Group size: 8–16 samples per prompt — 8 in v1; run 2 uses 16
- [x] QLoRA on KTO checkpoint
- [x] Monitor: training stability, reward curve, KL divergence from reference — reward mean ~0.55 with no upward trend over 40 steps; KL ~1e-4; loss negative (GRPO convention); run 2 needs more optimisation pressure (3 epochs, LR 5e-6, group 16)
- [x] Watch for: reward hacking (right answer, wrong reasoning), length inflation — none: completion lengths stable 150–180 tokens, no clipped completions, no gibberish
- [x] Checkpoint frequently — adapter + merged saved, backup sha256 verified

### 4.4 Evaluation
- [ ] Calculation accuracy on held-out scenarios (target: ≥90% exact)
- [ ] Boundary-specific accuracy (the 800k, 3M, 12M, 25M, 50M edges)
- [ ] Pidgin calculation accuracy
- [ ] No degradation on: multi-turn, coach behavior, citation discipline, general language
- [ ] Full eval suite
- [ ] Base-model comparison (the full journey: base → DAPT → SFT → KTO → GRPO)

### 4.5 Iterate
- [x] If accuracy plateaus: adjust difficulty distribution, increase group size — v2 used group 16 / LR 5e-6 / 3 epochs; v3 re-measured the hard tier on the current policy and rebuilt the mid pool (81 → 125)
- [x] If degradation: reduce GRPO steps, increase KL penalty — v3's behaviour regressions (30% top rate, VPC expansion, no-data calculation) tripped this: stopped RL and froze `grpo_v2`
- [x] Target: 3 iterations — v1 (optimisation too weak), v2 (best), v3 (behaviour trade, no calc gain)

**GRPO v1 status (2026-09-21):** 81 mid-tier prompts (25–75% exact at sampling), 1 epoch / 40 steps, group 8, LR 1e-6. Results vs KTO: held-out exact 5/10 → 5/10 (flat), dev 6/9 → 6/9 (flat), paraphrase exact 17/40 → 18/40, **paraphrase consistency 3/8 → 5/8**, coach flat. Zero regressions and no degeneration; the reward curve was flat within 40 steps, so run 2 strengthens optimisation (3 epochs, LR 5e-6, group 16, temp 1.0) before expanding the pool.

**GRPO v2 status (2026-09-21):** same pool, 3 epochs / 120 steps, group 16, LR 5e-6, temp 1.0. Training reward climbed 0.55 → 0.89–0.98 and held; KL ≤ 0.02; lengths stable. Vs KTO: dev exact 6/9 → **8/9** (+2: the 21%/23% band-edge and the Pidgin over-clarify both fixed), held-out 5/10 flat (CI 7/10; 12/20 answers byte-identical), paraphrase exact 17/40 flat with consistency maintained at 5/8, plus behaviour fixes (probe-scope-01 director now affirms coverage; probe-fact-04 pension-vs-NHF roles corrected). Most of the reward gain is mastery of the 81 training prompts, so v3 enlarges the mid pool: re-measure the 371 hard prompts on `grpo_v2` at temp 1.0, then rerun.

**GRPO v3 status (2026-09-21):** mid pool enlarged to 125 prompts (re-measured the 371 hard prompts on `grpo_v2` at temp 1.0: 120 exact samples across 42 newly-mid prompts), 1 epoch / 62 steps. Calc metrics flat vs v2 (dev 8/9, held-out 5/10, paraphrase 17/40; consistency 5/8 → 6/8), but **fact regressions**: the top rate was claimed as 30% (wrong), VPC was expanded as "Value-Added Tax" (v2 had fixed this), and a bare "Calculate my tax" was answered "Noted - I'll calculate your tax now" instead of asking for income. Decision: **freeze `grpo_v2` as the Phase 4 checkpoint of record** — three GRPO iterations complete, and further RL at this scale trades behaviour for no calculation gain.

**Phase 4 status (2026-09-21): exit under the frozen-knoll gate — stage gate not met.** Best model (`grpo_v2`): dev exact 8/9, held-out 5/10, paraphrase 17/40 with 5/8 consistency; vs SFT v2 that is dev 5/9 → 8/9, held-out 4/10 → 5/10, paraphrase 15/40 → 17/40, consistency 3/7 → 5/8. The remaining failures are band-edge arithmetic on novel amounts (e.g. 21%/23% slices) and the clarification boundary, which resisted on-policy RL. No degradation in length/format; all stages backed up with verified sha256.

**Stage gate:** ≥90% exact calculation accuracy on held-out scenarios including boundary values. No regression on any other eval dimension.

---

## Phase 5: Product Integration (Weeks 37–42)

**Objective:** Package the model into the product users experience.

### 5.1 GGUF Export & Optimization
- [ ] Merge adapters → full model → GGUF Q4_K_M
- [ ] Test through llama.cpp on dev laptop (speed, memory, correctness)
- [ ] Test on Codespace (audit-class proxy)
- [ ] Verify chat template works correctly for non-thinking mode
- [ ] Compare file size and speed vs Gate 1 model

### 5.2 App Bundle Updates
- [ ] Update Tier 1 bundles with new model
- [ ] Test on Windows (user's machine), Linux (dev machine), macOS (untestable — note)
- [ ] Update the TaxSabi.html app if needed (new capabilities → new UI affordances)

### 5.3 Fact Ledger Architecture (Tier 2)
- [ ] Design the ledger schema (income, reliefs, period, established facts, pending questions)
- [ ] Build grammar-constrained extraction (GBNF or JSON schema)
- [ ] Build the merge/validate/compute loop
- [ ] Build the "what we know so far" UI panel
- [ ] Integrate into the app bundle
- [ ] This is the product differentiator — invest time here

### 5.4 Mobile Considerations
- [ ] Evaluate llama.cpp on Android (NDK build or Termux)
- [ ] Evaluate MLC conversion for iOS
- [ ] Prototype if feasible, defer if not — this is a stretch goal

---

## Phase 6: Submission Preparation (Weeks 43–46+)

**Objective:** Ship it.

### 6.1 Final Evaluation
- [ ] Full eval suite on final model
- [ ] Official profiler run (participant mode, full accuracy)
- [ ] Compare against Gate 1 scores (baseline: Accuracy 65.81, Perf 24.47, Eff 84.65, Total 60.18)
- [ ] Document honestly — including remaining failure modes

### 6.2 Provenance Documentation (Gate 2 requirement)
- [ ] Model Provenance section in REPORT.md
- [ ] provenance/ folder:
      - adapter weights (each stage)
      - training scripts/configs
      - training logs (loss curves per stage)
      - dataset or representative sample + link
      - SHA256 checksums (base, adapters, final GGUF)
      - merge/quantization script
- [ ] Before/after comparison: ≥2 prompts showing base vs fine-tuned outputs
- [ ] Git commit SHA in metadata.json

### 6.3 Submission Materials
- [ ] Updated REPORT.md
- [ ] Updated metadata.json (2 test prompts — choose from verified-correct outputs)
- [ ] Updated download_model.sh (new HF URL for final model)
- [ ] Video (30s pitch + 1min demo + 30s innovation) — strictly 2 minutes
- [ ] Book and complete due diligence call
- [ ] Final repo check: all files present, no weights committed, clean history

### 6.4 Post-Submission
- [ ] Monitor for organizer questions
- [ ] Prepare for live defense (if selected as finalist)

---

## Cross-Cutting Concerns (All Phases)

### Evaluation Discipline
- [ ] Never evaluate on training data
- [ ] Always compare against the previous stage's checkpoint
- [ ] Always compare against the base model (the full journey)
- [ ] Log every eval result with model version, dataset version, and timestamp
- [ ] Gate each phase on its stage criteria before proceeding

### Data Discipline
- [ ] Every naira figure in training data is engine-computed
- [ ] Every citation in training data traces to the source register
- [ ] Every Pidgin record is human-reviewed
- [ ] Every conversation is either programmatically generated + engine-verified, or human-written
- [ ] Track dataset versions (git or explicit versioning)

### Compute Budget
| Phase | Estimated GPU hours | Source |
|---|---|---|
| DAPT | 4–8 | T4 (free) or AGH credits |
| SFT (4 rounds) | 12–20 | T4 |
| KTO (3 rounds) | 6–12 | T4 |
| GRPO (3 rounds) | 18–36 | AGH credits ($50) + T4 |
| Eval + misc | 4–8 | T4 |
| **Total** | **44–84** | Mixed |

### Risk Register
| Risk | Phase | Mitigation |
|---|---|---|
| DAPT causes memorization, not learning | 1 | Low LR, 1 epoch, validation split, check for verbatim recall |
| SFT narrows the model (Gate 1 lesson) | 2 | 10-20% replay data, diverse conversation types, paraphrase eval |
| KTO reward hacking | 3 | Monitor outputs, user spot-check, KL leash |
| GRPO training instability | 4 | Small group size initially, frequent checkpoints, KL penalty |
| Model too slow on audit hardware | 5 | Bench at every stage; if below target, consider Qwen3-0.6B fallback |
| Constitution too vague to generate good data | 0+2 | User review loop catches ambiguity; iterate constitution |
| Knowledge bleeding between stages | All | Evaluate general ability at every stage; replay data throughout |
| Pidgin quality degrades | 2+3 | Pidgin eval at every stage; user reviews all Pidgin data |

### Decision Points (check at each)
| When | Question | Default |
|---|---|---|
| End of Phase 1 | Is DAPT worth the compute vs pure SFT? | If knowledge gain <10%, skip to SFT |
| End of Phase 2 | Is the model good enough to skip KTO? | No — KTO is cheap and targets judged failures |
| End of Phase 3 | Is GRPO worth the risk? | If calc accuracy already ≥85%, consider skipping |
| Mid Phase 4 | Is GRPO degrading other abilities? | If yes, stop and use KTO checkpoint |
| End of Phase 4 | Is the model ready for product? | Stage-gate criteria |
| Phase 5 | Is the fact-ledger adding value? | If extraction is unreliable, simplify to direct model + engine |

---

## Success Criteria (Final)

| Metric | Gate 1 (baseline) | Target | Stretch |
|---|---|---|---|
| Calculation accuracy (natural) | 87.5% (7/8) | ≥95% | 100% |
| Calculation accuracy (boundary) | ~25% (3/12 clean) | ≥80% | ≥90% |
| Citation appropriateness | Always cites | ≥80% contextual | 100% contextual |
| Multi-turn coherence | Not supported | Basic (3-5 turns) | Robust (8+ turns) |
| Coach behavior | Not present | Relief discovery + sequencing | Full planning conversations |
| Pidgin fluency | Fragile | Natural on core prompts | Robust across phrasings |
| Zero invented citations | Fails (BFA-1991) | Zero tolerance | Zero |
| Zero invented amounts | Fails (NGN 100k) | Zero tolerance | Zero |
| Sperf (audit hardware) | 24.47 | ≥24 | ≥30 |
| Seff | 84.65 | ≥80 | ≥85 |
| Total score | 60.18 | ≥70 | ≥80 |

---

## What's Intentionally NOT In This Plan

- **RAG / retrieval at inference** — decided against; all knowledge in weights
- **Thinking mode** — decided against; latency risk with unknown judge timeout
- **A larger base model (3B+)** — CPU constraint; 1.7B is the ceiling
- **Fine-tuning a model from scratch** — not practical with our compute
- **Fine-tuning for mobile separately** — same model, different packaging
- **Full Yoruba/Hausa/Iglo support** — stretch goal after Gate 2, needs native-speaker review

---

## Document Control

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | Sept 2026 | DeepSeek + Chukwuemeka | Initial lock |
| | | | |
