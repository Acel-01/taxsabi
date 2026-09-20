# SFT Dataset v3 (top-up: rent drills, boundaries, clarify, facts) — Manifest

- Assembled: 2026-09-20 from verified layers + OASST1 replay
- Total examples: 2021 (train 1920 / val 101)
- Assistant words (core+replay): 99,677
- Duplicates removed: 77
- Eval overlap: none

| Source | Total | Train | Val | File | sha256 |
|---|---:|---:|---:|---|---|
| layer_a | 298 | 284 | 14 | `data/sft_verified_v2/layer_a.jsonl` | 8e6c24e303b96172 |
| layer_b | 77 | 70 | 7 | `data/sft_verified_v2/layer_b.jsonl` | ba8f3e574347ea26 |
| layer_c | 107 | 106 | 1 | `data/sft_verified_v2/layer_c.jsonl` | 29c39e4974706cc5 |
| single_en | 1077 | 1026 | 51 | `data/sft_verified_v2/single_en.jsonl` | ce8d5e7bab61cfe0 |
| single_pcm | 151 | 140 | 11 | `data/sft_verified_v2/single_pcm.jsonl` | 918d2898a2c6e9cd |
| topup_v3 | 92 | 89 | 3 | `data/sft_verified_v2/topup_v3.jsonl` | a172aad189375ca1 |
| replay | 219 | 205 | 14 | `data/sft_generated/replay_en.jsonl` | c434f0bd5e911627 |

Replay share: 10.8% of examples (219 OASST1 general-chat conversations)

Answer format: headline first (total tax / saving / citation), then the working.
