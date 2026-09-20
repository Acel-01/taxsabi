#!/usr/bin/env python3
"""QLoRA SFT (Unsloth) for TaxSabi — supports multi-turn conversations.

Consumes JSONL records with a `turns` list ([{role, content}, ...], roles
user/assistant alternating, starting with user) or legacy `instruction`/
`output` pairs. Loss is computed on assistant tokens only: system and user
turns are masked with -100, and each assistant turn trains on its content and
the end-of-turn token (the assistant header is masked).

Saves:
  <out>/adapter   - LoRA adapter
  <out>/merged    - merged fp16 model (best effort)
  <out>/gguf      - GGUF q4_k_m (best effort)

Local check without a GPU (renders samples and prints the mask):
  uv run python scripts/finetune_qlora.py --model unsloth/Qwen3-1.7B \
      --train data/sft_v1/train.jsonl --out /tmp/sft_dry --dry-run 3

Training (GPU):
  python scripts/finetune_qlora.py --model path/to/merged-dapt \
      --train data/sft_v1/train.jsonl --out ~/models/sft_v1
"""
import argparse
import json
import os
import random
import sys


def load_jsonl(path, max_records=None):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("turns"):
                rows.append(row)
            elif row.get("instruction") and row.get("output"):
                rows.append(row)
            if max_records and len(rows) >= max_records:
                break
    return rows


def get_tpl_kwargs(model_id):
    if "Qwen3" in model_id or "Qwen3" in model_id.split("/")[-1]:
        return {"enable_thinking": False}
    return {}


def render_conversation(tokenizer, system, turns, max_seq_len, tpl_kwargs):
    """Render a conversation with assistant-only labels. Returns (ids, labels, truncated)."""
    messages = [{"role": "system", "content": system}] + [
        {"role": turn["role"], "content": turn["content"]} for turn in turns
    ]

    def render(msgs, generation_prompt):
        return tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=generation_prompt, **tpl_kwargs
        )

    def tok(text):
        return tokenizer(text, add_special_tokens=False).input_ids

    input_ids, labels = [], []
    prev_text = ""
    for i, msg in enumerate(messages):
        if msg["role"] == "assistant":
            header_prefix = render(messages[:i], True)
            header_ids = tok(header_prefix[len(prev_text):])
            full_block = render(messages[:i + 1], False)
            body_ids = tok(full_block[len(header_prefix):])
            input_ids += header_ids + body_ids
            labels += [-100] * len(header_ids) + body_ids
            prev_text = full_block
        else:
            block = render(messages[:i + 1], False)
            seg_ids = tok(block[len(prev_text):])
            input_ids += seg_ids
            labels += [-100] * len(seg_ids)
            prev_text = block

    truncated = False
    if len(input_ids) > max_seq_len:
        overflow = len(input_ids) - max_seq_len
        input_ids = input_ids[overflow:]
        labels = labels[overflow:]
        truncated = True
    return input_ids, labels, truncated


def legacy_ids(tokenizer, system, row, max_seq_len, tpl_kwargs):
    prompt = tokenizer.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": row["instruction"]}],
        tokenize=False, add_generation_prompt=True, **tpl_kwargs,
    )
    full = prompt + row["output"] + tokenizer.eos_token
    full_ids = tokenizer(full, add_special_tokens=False).input_ids
    prompt_ids = tokenizer(prompt, add_special_tokens=False).input_ids
    labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids):]
    return full_ids[:max_seq_len], labels[:max_seq_len], len(full_ids) > max_seq_len


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="unsloth/Qwen3-1.7B")
    ap.add_argument("--train", required=True, help="training JSONL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--micro-batch", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--lora-alpha", type=int, default=128)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--system-prompt", default=(
        "You are an assistant that answers questions about Nigerian individual "
        "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
    ))
    ap.add_argument("--dry-run", type=int, default=0, metavar="N",
                    help="render N samples with the tokenizer and print the mask, then exit")
    args = ap.parse_args()

    tpl_kwargs = get_tpl_kwargs(args.model)
    rows = load_jsonl(args.train)
    print(f"loaded {len(rows)} training records from {args.train}")
    if not rows:
        raise SystemExit("no training records")

    if args.dry_run:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(args.model)
        truncated = 0
        lengths = []
        for row in rows:
            if row.get("turns"):
                ids, labels, trunc = render_conversation(
                    tokenizer, args.system_prompt, row["turns"], args.max_seq_len, tpl_kwargs
                )
            else:
                ids, labels, trunc = legacy_ids(
                    tokenizer, args.system_prompt, row, args.max_seq_len, tpl_kwargs
                )
            truncated += trunc
            lengths.append(len(ids))
        print(f"tokens: min {min(lengths)} / avg {sum(lengths)//len(lengths)} / max {max(lengths)}"
              f" | truncated: {truncated}")
        print()
        shown = 0
        for row in rows:
            if not row.get("turns") or shown >= args.dry_run:
                continue
            ids, labels, _ = render_conversation(
                tokenizer, args.system_prompt, row["turns"], args.max_seq_len, tpl_kwargs
            )
            trained = tokenizer.decode([i for i, l in zip(ids, labels) if l != -100])
            masked = tokenizer.decode([i for i, l in zip(ids, labels) if l == -100])
            print("=" * 70)
            print(f"{row['id']} | turns={len(row['turns'])} | tokens={len(ids)}")
            print("-- trained (loss) --")
            print(trained[:400].replace("\n", " \\n "))
            print("-- masked (context) --")
            print(masked[:300].replace("\n", " \\n "))
            shown += 1
        raise SystemExit(0)

    import torch
    # Unsloth must be imported before transformers/trl so its patches apply.
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from datasets import Dataset
    from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_len,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    encoded = []
    truncations = 0
    for row in rows:
        if row.get("turns"):
            ids, labels, trunc = render_conversation(
                tokenizer, args.system_prompt, row["turns"], args.max_seq_len, tpl_kwargs
            )
        else:
            ids, labels, trunc = legacy_ids(
                tokenizer, args.system_prompt, row, args.max_seq_len, tpl_kwargs
            )
        truncations += trunc
        encoded.append({"input_ids": ids, "labels": labels})
    del rows
    print(f"encoded {len(encoded)} records | truncated: {truncations}")
    train_dataset = Dataset.from_list(encoded)
    del encoded

    collator = DataCollatorForSeq2Seq(tokenizer, label_pad_token_id=-100)

    args_dict = dict(
        output_dir=os.path.join(args.out, "checkpoints"),
        per_device_train_batch_size=args.micro_batch,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
        seed=args.seed,
        dataloader_drop_last=True,
    )
    use_fp16 = not is_bfloat16_supported()
    args_dict["fp16"] = use_fp16
    args_dict["bf16"] = not use_fp16
    print("mixed precision:", "fp16" if use_fp16 else "bf16")

    trainer_kwargs = dict(
        model=model,
        args=TrainingArguments(**args_dict),
        train_dataset=train_dataset,
        data_collator=collator,
    )
    try:
        trainer = Trainer(tokenizer=tokenizer, **trainer_kwargs)
    except TypeError as exc:
        if "tokenizer" not in str(exc):
            raise
        trainer = Trainer(processing_class=tokenizer, **trainer_kwargs)
    result = trainer.train()
    print(f"training_loss: {result.training_loss:.4f}")

    model.save_pretrained(os.path.join(args.out, "adapter"))
    tokenizer.save_pretrained(os.path.join(args.out, "adapter"))

    merged_dir = os.path.join(args.out, "merged")
    os.makedirs(merged_dir, exist_ok=True)
    # Unsloth's merge copies read-only base weights from the HF cache; make them writable.
    import subprocess
    cache_root = os.path.join(
        os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")), "hub"
    )
    if os.path.exists(cache_root):
        subprocess.run(["chmod", "-R", "u+w", cache_root], check=False, capture_output=True)
    try:
        if not hasattr(model, "save_pretrained_merged"):
            raise AttributeError("save_pretrained_merged not available")
        model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")
        print("merged model saved to", merged_dir)
    except Exception as error:  # noqa: BLE001
        print(f"save_pretrained_merged failed ({type(error).__name__}: {error})")
        try:
            print("falling back to in-memory merge_and_unload ...")
            merged_model = model.merge_and_unload()
            merged_model.save_pretrained(merged_dir)
            tokenizer.save_pretrained(merged_dir)
            print("merged model saved to", merged_dir)
        except Exception as error2:  # noqa: BLE001
            print(f"merge fallback failed too ({type(error2).__name__}: {error2})")
            print("adapter saved; merge later with scripts/merge_adapter.py")

    try:
        try:
            model.save_pretrained_gguf(
                os.path.join(args.out, "gguf"), tokenizer, quantization_method="q4_k_m"
            )
        except TypeError:
            model.save_pretrained_gguf(
                os.path.join(args.out, "gguf"), quantization_method="q4_k_m"
            )
        print("GGUF saved under", os.path.join(args.out, "gguf"))
    except Exception as exc:  # noqa: BLE001
        print(f"GGUF export skipped ({type(exc).__name__}: {exc})")

    metadata = {"model": args.model, "train": args.train, "records": len(train_dataset),
                "epochs": args.epochs, "lr": args.lr, "lora_r": args.lora_r,
                "training_loss": result.training_loss}
    with open(os.path.join(args.out, "sft_run.json"), "w") as fh:
        json.dump(metadata, fh, indent=2)


if __name__ == "__main__":
    main()
