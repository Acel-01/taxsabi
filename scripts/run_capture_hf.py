#!/usr/bin/env python3
"""Capture model answers for a prompt suite using HuggingFace transformers.

GPU counterpart of run_baseline.py for merged checkpoints that have not been
converted to GGUF: loads a merged model (optionally with a LoRA adapter),
renders prompts with the Qwen3 chat template (thinking off), and writes
captures in the same JSONL format so compare_captures.py works unchanged.

Used for the Phase 1.3 knowledge check and every intermediate stage eval
before the final GGUF is built.

Usage:
    python scripts/run_capture_hf.py \
      --model ~/models/dapt_qwen3_1.7b/merged \
      --prompts data/eval/probe_prompts_heldout.jsonl \
      --out data/captures/dapt_heldout.jsonl \
      --label dapt-qwen3-1.7b
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SYSTEM = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)


def load_model(model_id: str, adapter: str | None, device_map: str, dtype: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch_dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}[dtype]
    print(f"loading tokenizer from {adapter or model_id}")
    tokenizer = AutoTokenizer.from_pretrained(adapter or model_id)
    print(f"loading model {model_id} ({dtype}, {device_map})")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch_dtype, device_map=device_map
    )
    if adapter:
        from peft import PeftModel

        print(f"loading adapter {adapter}")
        model = PeftModel.from_pretrained(model, adapter)
        model = model.merge_and_unload()
    model.eval()
    return model, tokenizer


def render_prompt(tokenizer, system: str, user: str) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )


def answer(model, tokenizer, prompt: str, max_new_tokens: int, max_seq_len: int) -> str:
    import torch

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_seq_len)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="merged model dir or HF id")
    parser.add_argument("--adapter", default=None, help="optional LoRA adapter dir")
    parser.add_argument("--prompts", required=True, help="prompt JSONL")
    parser.add_argument("--out", required=True, help="output capture JSONL")
    parser.add_argument("--label", required=True, help="stage label")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM)
    parser.add_argument("--max-new-tokens", type=int, default=400)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--dtype", choices=["bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--device-map", default="auto")
    args = parser.parse_args()

    started = datetime.now(timezone.utc).isoformat()
    model, tokenizer = load_model(args.model, args.adapter, args.device_map, args.dtype)

    prompts = [json.loads(line) for line in open(args.prompts) if line.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done_ids: set[str] = set()
    if out_path.exists():
        done_ids = {
            json.loads(line)["id"]
            for line in out_path.read_text().splitlines()
            if line.strip()
        }
    pending = [record for record in prompts if record["id"] not in done_ids]
    if done_ids:
        print(f"resuming: {len(done_ids)} already captured, {len(pending)} to go")

    t0 = time.time()
    count = 0
    with open(out_path, "a" if done_ids else "w") as fh:
        for record in pending:
            prompt = render_prompt(tokenizer, args.system_prompt, record["prompt"])
            text = answer(model, tokenizer, prompt, args.max_new_tokens, args.max_seq_len)
            row = {
                "id": record["id"],
                "language": record.get("language", "en"),
                "category": record.get("category", "unknown"),
                "prompt": record["prompt"],
                "answer": text,
                "label": args.label,
                "model": args.model,
                "thinking": False,
                "captured_at": started,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            count += 1
            print(f"[{count}/{len(pending)}] {record['id']}: {text[:70].replace(chr(10), ' ')}...", flush=True)
    elapsed = time.time() - t0
    print(f"\ncaptured {count} outputs in {elapsed / 60:.1f} min -> {args.out}")


if __name__ == "__main__":
    main()
