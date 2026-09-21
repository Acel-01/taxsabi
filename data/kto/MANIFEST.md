# KTO Dataset v1 — Manifest

- Assembled: 2026-09-21 from `data/kto/prompts.jsonl` + `data/kto/samples.jsonl`
- On-policy samples: model `/home/shadeform/models/sft_v2/merged` | temperature 0.8 | 3 per prompt
- Total examples: 3144 (train 2984 / val 160)
- Gold (verified) examples: 552 | on-policy samples: 2592
- On-policy desirable rate: 1236/2592 = 48%
- Gold labeler check failures: 0

| Type | Samples | Desirable | Rate |
|---|---:|---:|---:|
| clarify_ask | 36 | 3 | 8% |
| single_calc | 1650 | 707 | 43% |
| single_counterfactual | 252 | 168 | 67% |
| single_fact | 522 | 325 | 62% |
| single_fact_cited | 132 | 33 | 25% |

| Split | Total | Desirable | Undesirable |
|---|---:|---:|---:|
| train | 2984 | 1694 | 1290 |
| val | 160 | 94 | 66 |

Top label reasons: total_mismatch (941), total_exact (707), terms_and_citation_clean (358), missing_terms (274), saving_exact (163), saving_mismatch (72), computed_instead_of_asking (33), unauthorised_amounts (20)

Input sha256: prompts be0f81f86d2fa163 | samples 881c5b4c7a0d6b0a

Label protocol: deterministic rules only (engine totals, engine savings,
required terms, citation register). Verified gold answers always desirable.
