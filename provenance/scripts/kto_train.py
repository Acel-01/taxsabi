#!/usr/bin/env python3
"""KTO (Kahneman-Tversky Optimization) training for TaxSabi — Phase 3.2.

Trains a LoRA adapter on the binary-labelled dataset assembled by
`scripts/label_kto_samples.py` (columns: prompt/completion message lists +
bool label). Uses Unsloth's FastLanguageModel with TRL's KTOTrainer.

Checks without a GPU:
    # schema + class balance only (no model needed)
    uv run python scripts/kto_train.py --train data/kto/train.jsonl --check
    # render N samples with the tokenizer (needs transformers)
    python scripts/kto_train.py --model ~/models/sft_v2/merged \
        --train data/kto/train.jsonl --out /tmp/kto_dry --dry-run 3

Training (GPU):
    python scripts/kto_train.py --model ~/models/sft_v2/merged \
        --train data/kto/train.jsonl --val data/kto/val.jsonl \
        --out ~/models/kto_v1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter


def load_jsonl(path, require_messages=True):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if require_messages:
                prompt = row.get("prompt")
                completion = row.get("completion")
                if not (isinstance(prompt, list) and prompt and all("role" in m for m in prompt)):
                    raise SystemExit(f"bad `prompt` in {row.get('id')}: expected message list")
                if not (isinstance(completion, list) and completion and all("role" in m for m in completion)):
                    raise SystemExit(f"bad `completion` in {row.get('id')}: expected message list")
                if not isinstance(row.get("label"), bool):
                    raise SystemExit(f"bad `label` in {row.get('id')}: expected bool")
            rows.append(row)
    return rows


def check(args):
    rows = load_jsonl(args.train)
    train_counts = Counter(row["label"] for row in rows)
    print(f"train: {len(rows)} rows | desirable {train_counts[True]} / undesirable {train_counts[False]}")
    gold = sum(1 for row in rows if row.get("source") == "gold")
    types = Counter(row.get("type") for row in rows)
    print(f"  gold {gold} | on-policy {len(rows) - gold} | types {dict(types)}")
    if not train_counts[True] or not train_counts[False]:
        raise SystemExit("FAIL: KTO needs both desirable and undesirable examples")
    if args.val:
        val_rows = load_jsonl(args.val)
        val_counts = Counter(row["label"] for row in val_rows)
        print(f"val: {len(val_rows)} rows | desirable {val_counts[True]} / undesirable {val_counts[False]}")
    print("dataset check: OK")


def disable_thinking(tokenizer):
    """Force enable_thinking=false for every apply_chat_template call (Qwen3)."""
    template = getattr(tokenizer, "chat_template", None)
    if not isinstance(template, str) or "enable_thinking" not in template:
        return
    if template.lstrip().startswith("{%- set enable_thinking"):
        return
    tokenizer.chat_template = "{%- set enable_thinking = false %}\n" + template


def dry_run(args):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    disable_thinking(tokenizer)
    rows = load_jsonl(args.train)
    lengths = []
    for row in rows:
        prompt_text = tokenizer.apply_chat_template(
            row["prompt"], tokenize=False, add_generation_prompt=True
        )
        completion_text = row["completion"][0]["content"]
        ids = tokenizer(prompt_text + completion_text, add_special_tokens=False).input_ids
        lengths.append(len(ids))
    print(f"tokens: min {min(lengths)} / avg {sum(lengths)//len(lengths)} / max {max(lengths)}")
    for row in rows[: args.dry_run]:
        prompt_text = tokenizer.apply_chat_template(
            row["prompt"], tokenize=False, add_generation_prompt=True
        )
        print("=" * 70)
        print(f"{row['id']} | label={row['label']} | type={row.get('type')} | reason={row.get('reason')}")
        print("-- prompt --")
        print(prompt_text[-500:].replace("\n", " \\n "))
        print("-- completion (trained span) --")
        print(row["completion"][0]["content"][:400].replace("\n", " \\n "))
    print("\ndry run: OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="unsloth/Qwen3-1.7B", help="merged SFT checkpoint")
    ap.add_argument("--train", required=True)
    ap.add_argument("--val", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--epochs", type=float, default=1)
    ap.add_argument("--lr", type=float, default=5e-6)
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--micro-batch", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--lora-alpha", type=int, default=128)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--check", action="store_true", help="validate dataset only (no model)")
    ap.add_argument("--dry-run", type=int, default=0, metavar="N",
                    help="render N samples with the tokenizer, then exit")
    args = ap.parse_args()

    if args.check:
        check(args)
        return

    if not args.model:
        raise SystemExit("--model is required")
    if not args.out and not args.dry_run:
        raise SystemExit("--out is required for training")

    if args.dry_run:
        dry_run(args)
        return

    import torch
    # Unsloth must be imported before transformers/trl so its patches apply.
    from unsloth import FastLanguageModel
    try:
        from unsloth import PatchFastRL
        PatchFastRL("KTO", FastLanguageModel)
    except ImportError:
        pass
    from trl import KTOConfig, KTOTrainer
    from datasets import Dataset

    torch.manual_seed(args.seed)
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
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )
    disable_thinking(tokenizer)

    def to_dataset(path):
        rows = load_jsonl(path)
        return Dataset.from_list([
            {"prompt": row["prompt"], "completion": row["completion"], "label": row["label"]}
            for row in rows
        ])

    train_dataset = to_dataset(args.train)
    eval_dataset = to_dataset(args.val) if args.val else None
    print(f"train examples: {len(train_dataset)} | val: {len(eval_dataset) if eval_dataset else 0}")

    config_kwargs = dict(
        output_dir=os.path.join(args.out, "checkpoints"),
        per_device_train_batch_size=args.micro_batch,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_strategy="epoch",
        optim="adamw_8bit",
        beta=args.beta,
        max_length=args.max_seq_len,
        max_prompt_length=args.max_seq_len // 2,
        seed=args.seed,
        report_to="none",
    )
    try:
        import inspect
        supported = set(inspect.signature(KTOConfig.__init__).parameters)
        config_kwargs = {key: value for key, value in config_kwargs.items() if key in supported}
    except (TypeError, ValueError):
        pass
    config = KTOConfig(**config_kwargs)
    print("KTO config:", {key: value for key, value in config_kwargs.items() if key != "output_dir"})

    trainer_kwargs = dict(
        model=model,
        ref_model=None,
        args=config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
    try:
        trainer = KTOTrainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError as exc:
        if "processing_class" not in str(exc):
            raise
        trainer = KTOTrainer(tokenizer=tokenizer, **trainer_kwargs)

    result = trainer.train()
    print(f"training_loss: {result.training_loss:.4f}")

    model.save_pretrained(os.path.join(args.out, "adapter"))
    tokenizer.save_pretrained(os.path.join(args.out, "adapter"))

    merged_dir = os.path.join(args.out, "merged")
    os.makedirs(merged_dir, exist_ok=True)
    try:
        if not hasattr(model, "save_pretrained_merged"):
            raise AttributeError("save_pretrained_merged not available")
        model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")
        print("merged model saved to", merged_dir)
    except Exception as error:  # noqa: BLE001
        print(f"merge failed ({type(error).__name__}: {error}); use scripts/merge_adapter.py later")

    metadata = {
        "model": args.model,
        "train": args.train,
        "val": args.val,
        "train_examples": len(train_dataset),
        "epochs": args.epochs,
        "lr": args.lr,
        "beta": args.beta,
        "lora_r": args.lora_r,
        "training_loss": result.training_loss,
    }
    with open(os.path.join(args.out, "kto_run.json"), "w") as fh:
        json.dump(metadata, fh, indent=2)
    print("run metadata ->", os.path.join(args.out, "kto_run.json"))


if __name__ == "__main__":
    main()
