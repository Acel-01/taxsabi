# Base Model Baseline — Qwen3-1.7B (un-tuned)

**Model:** Qwen3-1.7B-Q4_K_M.gguf (unsloth/Qwen3-1.7B-GGUF)
**SHA256:** b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897
**Thinking mode:** disabled (chat_template_kwargs enable_thinking=false)
**Temperature:** 0.0
**Benchmark (dev laptop, i5-8250U @1.6GHz, 4 threads):** 20.89 t/s prompt processing, 6.09 t/s generation
**Prompts:** 30 (20 English + 10 Pidgin) — `data/eval/baseline_prompts.jsonl`
**Outputs:** `data/eval/baselines/base_qwen3_1.7b.jsonl`

## Findings

### 1. Static knowledge — confabulated

| Prompt | Base model answered | Correct answer |
|---|---|---|
| Tax bands (en-01) | "Basic Personal Income Tax: 15% up to N1.5 million" | 0% first 800k; 15% next 2.2m; 18% next 9m; 21% next 13m; 23% next 25m; 25% above 50m |
| Rent relief (en-02, en-07) | "10% of rent paid" + guessed rent of 50,000 | 20% of annual rent, capped at 500,000 |
| Exemptions (pcm-09) | "Basic exemption NGN 100,000 + additional NGN 50,000" | Zero band: first 800,000 at 0% |
| Standard rate (pcm-03) | "20% standard tax rate" | Progressive bands, no flat rate |
| NHF expansion (en-13) | "National Health Fund" | National Housing Fund |
| NHF/NHIS (pcm-10) | Confused the two; "mandatory... voluntary in the sense that they are not tax-deductible" | NHF voluntary for private sector (NHF Act 1992 s.4 as amended by BFA 2022 s.45); listed as deduction under NTA s.30(2)(a)(i) |
| Pension (pcm-05) | "Pension contribution is not tax-deductible" | Pension contributions ARE deductible under s.30(2)(a)(iii) |

### 2. Calculations — no direct answers

- The model never produced a numeric tax figure in any of the 10 calculation prompts
- Verbose hedging ("we need to consider..."), fabricated assumptions, invented reliefs
- en-07 (net income, the judge prompt): invented a 10% rent relief AND a 50,000 rent figure
- pcm-05: rendered "25m" as "N$25 million" (Namibian dollar) — currency symbol confusion

### 3. Scope behavior — partial

| Behavior | Result |
|---|---|
| Ghana tax (en-19, pcm-08) | ✅ Declined correctly ("I cannot calculate your Ghana personal income tax") |
| 2025 rules (en-18) | ❌ Did not decline — asked for details to calculate "2026" instead |
| Missing period (en-11, pcm-09) | ❌ Guessed assumptions instead of asking monthly/annual |
| PAYE (en-20) | ❌ Confident wrong steps ("Determine the Employer's Taxable Income") |

### 4. Language — Pidgin not supported

- All 10 Pidgin prompts were answered in English
- No Pidgin phrasing attempted
- NHF/NHIS tax content wrong in Pidgin too

### 5. Format

- Heavy markdown (###, **bold**, bullet lists), "Assumptions" sections
- Formal/verbose; not conversational
- Some answers truncated mid-table (max_tokens 400)

## Implications for Training

1. **DAPT has real work to do** — the base's tax knowledge is not just incomplete, it is *wrong and confident*. Facts must overwrite confabulations, not merely add to them.
2. **Citation behavior needs explicit training** — the base cites no sections (and has no correct ones to cite).
3. **Scope refusals partially exist** (Ghana declined) — SFT should preserve and extend this behavior, not teach it from zero.
4. **Pidgin is a from-scratch capability** — the base has none; our reviewed Pidgin data is the seed.
5. **The "before/after" Gate 2 requirement is satisfied** — these outputs contrast dramatically with even the Gate 1 v6c model.

## The Dramatic Contrast (for provenance)

Same prompt, base vs Gate 1 v6c:

**Prompt:** "I earn NGN 800,000 a year and no deductions or reliefs. How much tax do I pay?"

- **Base Qwen3-1.7B:** "To calculate the individual income tax for a Nigerian resident, we need to consider... Assumptions: You are a resident of Nigeria. You are not a self-employed..." (no answer)
- **TaxSabi v6c:** "Gross annual income: NGN 800,000. Chargeable income: NGN 800,000. Band calculation: NGN 800,000 at 0% = NGN 0. Estimated annual tax: NGN 0."
