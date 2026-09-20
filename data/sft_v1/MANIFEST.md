# SFT Dataset v1 — Manifest

- Assembled: 2026-09-20 from verified layers + OASST1 replay
- Total examples: 1929 (train 1833 / val 96)
- Assistant words (core+replay): 96,050
- Duplicates removed: 75
- Eval overlap: none

| Source | Total | Train | Val | File | sha256 |
|---|---:|---:|---:|---|---|
| layer_a | 298 | 284 | 14 | `data/sft_verified/layer_a.jsonl` | 1261a6d19bf28960 |
| layer_b | 77 | 71 | 6 | `data/sft_verified/layer_b.jsonl` | 66d0e96463d0b578 |
| layer_c | 107 | 100 | 7 | `data/sft_verified/layer_c.jsonl` | 8646516892412159 |
| single_en | 1077 | 1034 | 43 | `data/sft_verified/single_en.jsonl` | 0b325e258acb31a2 |
| single_pcm | 151 | 142 | 9 | `data/sft_verified/single_pcm.jsonl` | 2c8270466ad8ab4d |
| replay | 219 | 202 | 17 | `data/sft_generated/replay_en.jsonl` | c434f0bd5e911627 |

Replay share: 11.4% of examples (219 OASST1 general-chat conversations)

Answer format: headline first (total tax / saving / citation), then the working.
