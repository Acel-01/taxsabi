#!/usr/bin/env python3
"""Sample on-policy completions for the KTO prompt pool (GPU).

Generates `--samples` independent completions per prompt with temperature
sampling in batches, so the KTO labeler sees the model's own failure modes
(wrong totals, invented figures, over-clarification) alongside its good ones.

Resumes by (prompt_id, sample_index). Output rows:
    {"id": <prompt id>, "sample": <n>, "answer": "..."}

Runs on the instance (needs transformers + a GPU); the labeler runs locally.

Usage:
    python scripts/sample_kto_completions.py \
      --model ~/models/sft_v2/merged \
      --prompts data/kto/prompts.jsonl \
      --out data/kto/samples.jsonl \
      --samples 3 --temperature 0.8
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
    tokenizer = AutoTokenizer.from_pretrained(adapter or model_id)
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch_dtype, device_map=device_map
    )
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="merged model dir or HF id")
    parser.add_argument("--adapter", default=None, help="optional LoRA adapter dir")
    parser.add_argument("--prompts", required=True, help="KTO prompt pool JSONL")
    parser.add_argument("--out", required=True, help="output samples JSONL")
    parser.add_argument("--samples", type=int, default=3, help="completions per prompt")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-new-tokens", type=int, default=320)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="only sample N tasks (smoke test)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM)
    parser.add_argument("--dtype", choices=["bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--device-map", default="auto")
    args = parser.parse_args()

    import torch

    torch.manual_seed(args.seed)

    prompts = [
        json.loads(line)
        for line in open(args.prompts)
        if line.strip()
    ]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[tuple[str, int]] = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                done.add((row["id"], row["sample"]))
        print(f"resuming: {len(done)} samples already captured")

    tasks: list[tuple[dict, int]] = []
    for record in prompts:
        for index in range(args.samples):
            if (record["id"], index) not in done:
                tasks.append((record, index))
    if args.limit:
        tasks = tasks[: args.limit]
    if not tasks:
        print("nothing to do")
        return

    model, tokenizer = load_model(args.model, args.adapter, args.device_map, args.dtype)
    rendered: dict[str, str] = {}
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    count = 0

    with open(out_path, "a" if done else "w") as fh:
        for start in range(0, len(tasks), args.batch_size):
            batch = tasks[start:start + args.batch_size]
            texts = []
            for record, _ in batch:
                if record["id"] not in rendered:
                    rendered[record["id"]] = render_prompt(
                        tokenizer, args.system_prompt, record["prompt"]
                    )
                texts.append(rendered[record["id"]])
            inputs = tokenizer(
                texts, return_tensors="pt", padding=True,
                truncation=True, max_length=args.max_seq_len,
            )
            inputs = {key: value.to(model.device) for key, value in inputs.items()}
            generate_kwargs = dict(
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
            if args.temperature > 0:
                generate_kwargs.update(
                    do_sample=True, temperature=args.temperature, top_p=args.top_p
                )
            else:
                generate_kwargs.update(do_sample=False)
            with torch.no_grad():
                output = model.generate(**inputs, **generate_kwargs)
            generated = output[:, inputs["input_ids"].shape[1]:]
            for (record, index), tokens in zip(batch, generated):
                text = tokenizer.decode(tokens, skip_special_tokens=True).strip()
                row = {
                    "id": record["id"],
                    "sample": index,
                    "answer": text,
                    "type": record.get("type"),
                    "language": record.get("language"),
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
            fh.flush()
            elapsed = time.time() - t0
            rate = count / elapsed if elapsed else 0
            print(f"[{count}/{len(tasks)}] {rate:.1f} samples/s", flush=True)

    elapsed = time.time() - t0
    meta = {
        "model": args.model,
        "adapter": args.adapter,
        "prompts": args.prompts,
        "samples_per_prompt": args.samples,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
        "captured": count,
        "started_at": started,
        "elapsed_minutes": round(elapsed / 60, 1),
    }
    meta_path = out_path.parent / "sample_run.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"\nsampled {count} completions in {elapsed / 60:.1f} min -> {out_path}")
    print(f"run metadata -> {meta_path}")


if __name__ == "__main__":
    main()
