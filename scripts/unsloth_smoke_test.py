#!/usr/bin/env python3
"""Unsloth/Qwen3-1.7B environment smoke test for AGH or Colab.

Run this first on any new GPU environment before starting real training. It
verifies, in order:
  1. GPU + library versions
  2. Unsloth 4-bit load of the chosen model (default unsloth/Qwen3-1.7B)
  3. Qwen3 chat template with thinking disabled
  4. A short SFT run (a few steps on toy data) with a decreasing loss
  5. Availability of KTO and GRPO trainers for the later pipeline stages

Prereq (fresh environment, e.g. Colab T4 / AGH):
    pip install unsloth
    # (Colab also needs:) pip install --no-deps trl peft accelerate bitsandbytes

Usage:
    python scripts/unsloth_smoke_test.py
    python scripts/unsloth_smoke_test.py --model unsloth/Qwen3-1.7B --steps 8
"""
from __future__ import annotations

import argparse
import importlib
import sys


def version_of(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
        return getattr(module, "__version__", "unknown")
    except Exception as error:  # noqa: BLE001
        return f"NOT INSTALLED ({type(error).__name__})"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="unsloth/Qwen3-1.7B")
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--max-seq-len", type=int, default=512)
    args = parser.parse_args()

    print("=== 1. environment ===")
    import torch
    print(f"torch: {torch.__version__}")
    print(f"cuda available: {torch.cuda.is_available()}")
    print(f"rocm/hip build: {getattr(torch.version, 'hip', None) or 'no'}")
    if torch.cuda.is_available():
        print(f"gpu: {torch.cuda.get_device_name(0)}")
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"vram: {vram:.1f} GB")
    if not torch.cuda.is_available():
        print("note: Unsloth requires CUDA. On ROCm/CPU, use the HF PEFT stack instead.")
    for name in ("unsloth", "transformers", "trl", "peft", "accelerate", "bitsandbytes", "datasets"):
        print(f"{name}: {version_of(name)}")

    print("\n=== 2. Unsloth 4-bit load ===")
    from unsloth import FastLanguageModel, is_bfloat16_supported

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_len,
        dtype=None,
        load_in_4bit=True,
    )
    print(f"loaded: {args.model}")
    print(f"is_bfloat16_supported: {is_bfloat16_supported()}")

    print("\n=== 3. chat template (thinking off) ===")
    try:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": "What is the first tax band?"}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        print(f"template ok ({len(rendered)} chars)")
        print(rendered[:120].replace("\n", " ") + " ...")
    except Exception as error:  # noqa: BLE001
        print(f"template FAILED: {type(error).__name__}: {error}")
        sys.exit(1)

    print(f"\n=== 4. mini SFT ({args.steps} steps, toy data) ===")
    from datasets import Dataset
    from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    system = "You are an assistant that answers questions about Nigerian individual income tax."
    toy = [
        ("What is the first tax band?", "The first NGN 800,000 of chargeable income is taxed at 0% under the 2026 framework."),
        ("When is PAYE due?", "PAYE deducted from salaries is remitted by the 10th day of the following month."),
        ("What is rent relief?", "Rent relief is 20% of annual rent paid, capped at NGN 500,000."),
        ("Pension contribution limits?", "Voluntary contributions cannot exceed one-third of the month's salary."),
    ]
    texts = []
    for question, answer in toy:
        prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": question}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        texts.append(prompt + answer + tokenizer.eos_token)

    dataset = Dataset.from_dict({"text": texts})

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=args.max_seq_len)

    dataset = dataset.map(tokenize, batched=True, remove_columns=["text"])
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        train_dataset=dataset,
        data_collator=collator,
        args=TrainingArguments(
            output_dir="/tmp/unsloth_smoke",
            per_device_train_batch_size=2,
            gradient_accumulation_steps=1,
            max_steps=args.steps,
            learning_rate=2e-4,
            logging_steps=1,
            save_strategy="no",
            report_to="none",
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
        ),
    )
    result = trainer.train()
    print(f"training_loss: {result.training_loss:.4f}")
    if result.training_loss >= 20:
        print("warning: loss looks wrong for this toy data")

    print("\n=== 5. KTO / GRPO availability ===")
    for trainer_name in ("KTOTrainer", "GRPOTrainer", "DPOTrainer", "SFTTrainer"):
        try:
            module = importlib.import_module("trl")
            getattr(module, trainer_name)
            print(f"trl.{trainer_name}: available")
        except Exception as error:  # noqa: BLE001
            print(f"trl.{trainer_name}: NOT available ({type(error).__name__}: {error})")

    print("\n=== smoke test complete ===")
    print("If steps 1-4 passed, the environment can run DAPT and SFT.")
    print("For KTO/GRPO, install a trl version that provides the missing trainers.")


if __name__ == "__main__":
    main()
