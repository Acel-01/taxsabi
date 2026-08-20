#!/usr/bin/env python3
"""QLoRA fine-tune (Unsloth) for the NaijaTax Laptop LLM Challenge.

Designed to run on a Colab/Kaggle T4 (16 GB). Saves:
  <out>/adapter   - LoRA adapter
  <out>/merged    - merged fp16 model (load this in eval_qlora.py)
  <out>/gguf      - GGUF q4_k_m for llama.cpp (optional, best effort)

Example:
  python finetune_qlora.py --model Qwen/Qwen3-0.6B \
      --train data/train/final_english_v5.jsonl --out /content/models/en_qwen3_0.6b
"""
import argparse
import json
import os
import random


def load_jsonl(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not row.get("instruction") or not row.get("output"):
                continue
            rows.append(row)
    return rows

def get_tpl_kwargs(model_id):
    if "Qwen3" in model_id or "Qwen3" in model_id.split("/")[-1]:
        return {"enable_thinking": False}
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--train", required=True, help="training JSONL (verified dataset)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--micro-batch", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--lora-r", type=int, default=32)
    ap.add_argument("--lora-alpha", type=int, default=64)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
    from unsloth import FastLanguageModel, is_bfloat16_supported

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

    tpl_kwargs = get_tpl_kwargs(args.model)
    system = (
        "You are an assistant that answers questions about Nigerian individual "
        "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
    )

    def format_one(row):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": row["instruction"]},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            **tpl_kwargs,
        )
        full = prompt + row["output"] + tokenizer.eos_token
        full_ids = tokenizer(
            full,
            add_special_tokens=False,
            truncation=True,
            max_length=args.max_seq_len,
        ).input_ids
        prompt_ids = tokenizer(
            prompt,
            add_special_tokens=False,
            truncation=True,
            max_length=args.max_seq_len,
        ).input_ids
        labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids):]
        return {
            "input_ids": full_ids,
            "labels": labels,
        }

    rows = load_jsonl(args.train)
    print(f"loaded {len(rows)} training records from {args.train}")
    encoded = [format_one(r) for r in rows]
    del rows
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
        warmup_ratio=0.05,
        logging_steps=10,
        save_strategy="no",
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
    trainer.train()

    model.save_pretrained(os.path.join(args.out, "adapter"))
    tokenizer.save_pretrained(os.path.join(args.out, "adapter"))

    merged_dir = os.path.join(args.out, "merged")
    os.makedirs(merged_dir, exist_ok=True)
    if hasattr(model, "save_pretrained_merged"):
        model.save_pretrained_merged(
            merged_dir,
            tokenizer,
            save_method="merged_16bit",
        )
    else:
        merged_model = model.merge_and_unload()
        merged_model.save_pretrained(merged_dir)
        tokenizer.save_pretrained(merged_dir)
    print("merged model saved to", merged_dir)

    try:
        try:
            model.save_pretrained_gguf(
                os.path.join(args.out, "gguf"),
                tokenizer,
                quantization_method="q4_k_m",
            )
        except TypeError:
            model.save_pretrained_gguf(
                os.path.join(args.out, "gguf"),
                quantization_method="q4_k_m",
            )
        print("GGUF saved under", os.path.join(args.out, "gguf"))
    except Exception as exc:  # noqa: BLE001
        print(f"GGUF export skipped ({type(exc).__name__}: {exc})")

if __name__ == "__main__":
    main()
