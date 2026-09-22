# Merge and quantization

Base model: `unsloth/Qwen3-1.7B` at revision
`6262b50d6c1f8ee5e4ac750d710c33603bfc2a0c` (mirror of `Qwen/Qwen3-1.7B`,
Apache-2.0). The four stage adapters were merged sequentially onto that base with
`scripts/merge_adapter.py` (plain transformers + PEFT; `merge_and_unload()`):

```bash
python scripts/merge_adapter.py --base unsloth/Qwen3-1.7B \
  --adapter models/dapt_qwen3_1.7b_v5/adapter --out models/dapt_v5_merged --device cuda
python scripts/merge_adapter.py --base models/dapt_v5_merged \
  --adapter models/sft_v2/adapter --out models/sft_v2/merged --device cuda
python scripts/merge_adapter.py --base models/sft_v2/merged \
  --adapter models/kto_v1/adapter --out models/kto_v1/merged --device cuda
python scripts/merge_adapter.py --base models/kto_v1/merged \
  --adapter models/grpo_v2/adapter --out models/grpo_v2/merged --device cuda
```

The final adapter (`provenance/adapter_model.safetensors`, stage GRPO v2) is the
one that produced the submitted model; upstream stage adapters are archived in the
team's backups with SHA256 checksums.

GGUF export used Unsloth's converter on the merged checkpoint:

```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="models/grpo_v2/merged", max_seq_length=2048,
    dtype=None, load_in_4bit=False)
model.save_pretrained_gguf("models/grpo_v2/hq", tokenizer,
    quantization_method=["q4_k_m", "q5_k_m", "q6_k", "q8_0"])
```

## Why Q8_0 ships (quantization fidelity study)

Each candidate was tested through llama.cpp on the same 8-prompt sanity subset,
the 20-prompt held-out probe and the 30-prompt dev probe, and compared against the
full-precision (bf16) model's captures. Results:

| Quant | Held-out exact | Dev exact | 2026 band table | Notes |
|---|---:|---:|---|---|
| bf16 (reference) | 5/10 | 8/9 | correct on 4/6 phrasings | measured model |
| **Q8_0 (shipped)** | **5/10** | **8/9** | **4/6, identical pattern to bf16** | 12/20 held-out answers byte-identical |
| Q6_K | — | — | "four bands" (corrupt) | rejected |
| Q5_K_M | 5/10 | — | older/wrong band table | rejected |
| Q4_K_M | 1/5 on subset | — | "four bands"; arithmetic flips (rent relief 360k→300k; 700k zero band taxed) | rejected |

The shipped file is `model/TaxSabi-Qwen3-1.7B-Q8_0.gguf`
(1.70 GiB, SHA256
`4ff08c7008f75181b3b64cc7317d3cf494d1679eddc07643e6153644e203e8fc`).

Trade-off, stated plainly: Q8_0 is ~30–45% slower and ~0.6 GiB larger than
Q4_K_M, but Q4_K_M demonstrably corrupts core statutory knowledge (the 2026 band
table) and flips arithmetic on unseen amounts, so the higher-precision quant was
chosen to protect accuracy, which carries 50% of the score.
