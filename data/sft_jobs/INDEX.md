# SFT Job Blueprints

Training conversations were generated from the engine-locked blueprints in this
directory, then verified record-by-record with `scripts/verify_sft_generation.py`
before entering the training pools. Every number in a blueprint comes from the
Decimal rules engine in `src/rules_engine/`.

| Layer | Language | Blueprints | Batch files | Purpose |
|---|---|---:|---:|---|
| `layer_a` | en | 300 | 30 | Multi-turn conversations: accumulate-then-compute, counterfactual, correction, clarify-then-compute, topic shift, scope decline |
| `layer_b` | en | 80 | 8 | Coaching conversations: relief discovery, savings modelling, sequencing |
| `layer_c` | pcm | 110 | 11 | Pidgin versions of the Layer A conversation types |
| `single_en` | en | 1,140 | 46 | Single-turn calc / counterfactual / fact Q&A (three phrasings per calculation scenario) |
| `single_pcm` | pcm | 154 | 7 | Pidgin single-turn Q&A |
| `topup_v3` | en + pcm | 94 | 4 | Targeted drills for held-out failures: rent percentage, band boundaries, clarify boundaries, corrected facts |

The `batch_*.jsonl` files are the blueprint definitions (JSON, one record per
line). After generation, records are verified with
`scripts/verify_sft_generation.py` and only passing records enter `data/sft_v2/`.
