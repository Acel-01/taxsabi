# SFT Dataset v2 (working-first totals) — Manifest

- Assembled: 2026-09-20 from verified layers + OASST1 replay
- Total examples: 1929 (train 1833 / val 96)
- Assistant words (core+replay): 96,050
- Duplicates removed: 75
- Eval overlap: none

| Source | Total | Train | Val | File | sha256 |
|---|---:|---:|---:|---|---|
| layer_a | 298 | 284 | 14 | `data/sft_verified_v2/layer_a.jsonl` | 8e6c24e303b96172 |
| layer_b | 77 | 71 | 6 | `data/sft_verified_v2/layer_b.jsonl` | ba8f3e574347ea26 |
| layer_c | 107 | 100 | 7 | `data/sft_verified_v2/layer_c.jsonl` | 29c39e4974706cc5 |
| single_en | 1077 | 1034 | 43 | `data/sft_verified_v2/single_en.jsonl` | ce8d5e7bab61cfe0 |
| single_pcm | 151 | 142 | 9 | `data/sft_verified_v2/single_pcm.jsonl` | 918d2898a2c6e9cd |
| replay | 219 | 202 | 17 | `data/sft_generated/replay_en.jsonl` | c434f0bd5e911627 |

Replay share: 11.4% of examples (219 OASST1 general-chat conversations)

Answer format: headline first (total tax / saving / citation), then the working.
