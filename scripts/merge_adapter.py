#!/usr/bin/env python3
"""Merge a LoRA adapter into its base model using plain transformers + PEFT.

Unsloth's save_pretrained_merged can fail on read-only HF cache files or on
transformers weight-conversion quirks in unsloth-patched models. This
standalone path avoids unsloth entirely and is the reliable way to produce a
merged fp16 model for GGUF conversion or HF-format evaluation.

Usage:
    python scripts/merge_adapter.py \
      --base unsloth/Qwen3-1.7B \
      --adapter ~/models/dapt_qwen3_1.7b/adapter \
      --out ~/models/dapt_qwen3_1.7b/merged_hf
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="base model id or dir")
    parser.add_argument("--adapter", required=True, help="LoRA adapter dir")
    parser.add_argument("--out", required=True, help="output merged model dir")
    parser.add_argument("--dtype", choices=["bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--device", default="cpu", help="cpu (safe) or cuda")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}[args.dtype]
    print(f"loading base {args.base} ({args.dtype}, {args.device})")
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=dtype, device_map=args.device
    )
    print(f"applying adapter {args.adapter}")
    model = PeftModel.from_pretrained(base, args.adapter)
    merged = model.merge_and_unload()
    print(f"saving merged model -> {args.out}")
    merged.save_pretrained(args.out)
    AutoTokenizer.from_pretrained(args.adapter).save_pretrained(args.out)
    print("done")


if __name__ == "__main__":
    main()
