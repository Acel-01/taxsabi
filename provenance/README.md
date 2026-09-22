# Provenance — TaxSabi (ADTC 2026, team `taxsabi`)

This folder is the proof-of-training package for the submitted model
**TaxSabi-Qwen3-1.7B-Q8_0**.

## Contents

| Item | Purpose |
|---|---|
| `adapter_model.safetensors` + `adapter_config.json` | Final GRPO v2 LoRA adapter (trained on the KTO v1 checkpoint). Tracked with Git LFS (267 MB, over GitHub's 100 MB limit). |
| `scripts/` | Training and data pipeline that produced the model: `dapt_pretrain.py`, `finetune_qlora.py`, `kto_train.py`, `grpo_train.py`, `merge_adapter.py`, plus prompt/label builders and the engine verifier. |
| `runs/` | Run metadata (`dapt_run.json`, `sft_run.json`, `kto_run.json`, `grpo_run.json`) with final loss and hyperparameters. |
| `training_log.txt` | Stage-by-stage training summary and outcomes. |
| `grpo_v2_steps.csv` | Per-log-step GRPO metrics (reward, KL, loss) for the final stage. |
| `dataset_info.md` | Dataset names, sources, sizes and licenses. |
| `merge_quantize.md` | Merge + GGUF quantization commands and the quant fidelity study. |
| `checksums.txt` | SHA256 for the adapter, shipped GGUF and key dataset files. |

## Verification

```bash
sha256sum -c checksums.txt          # from the repository root
```

Expected adapter SHA256:
`720f81ded7e85a54db68b32d36b326e0d18a896a6f52a9ebae81ddeab4f7b3b7`

The adapter is applied to `unsloth/Qwen3-1.7B` at revision
`6262b50d6c1f8ee5e4ac750d710c33603bfc2a0c`, merged per `merge_quantize.md`, and
exported to the submitted Q8_0 GGUF.
