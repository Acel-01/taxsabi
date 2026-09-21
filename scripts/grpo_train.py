#!/usr/bin/env python3
"""GRPO training for TaxSabi — Phase 4, verifiable-reward RL on the engine.

Reward (per completion, from `scripts/build_grpo_pool.py` ground truth):
    final total tax exact (engine)        -> 1.0
    else chargeable income exact          -> 0.25
    else                                  -> 0.0
No negative rewards in v1; no thinking mode (the chat template is forced to
enable_thinking=false for every apply_chat_template call, matching SFT/KTO).

Checks without a GPU:
    uv run python scripts/grpo_train.py --pool data/grpo/pool.jsonl --check
    python scripts/grpo_train.py --model ~/models/kto_v1/merged \
        --pool data/grpo/train_pool.jsonl --out /tmp/grpo_dry --dry-run 3

Training (GPU):
    python scripts/grpo_train.py --model ~/models/kto_v1/merged \
        --pool data/grpo/train_pool.jsonl --out ~/models/grpo_v1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eval_qlora import CHARGEABLE_INCOME_RE, TOTAL_TAX_RE, extract_labeled_amount, norm_amount  # noqa: E402

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)


def load_pool(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("prompt") or not row.get("expected_total_tax"):
            continue
        rows.append(row)
    return rows


def tax_reward(completions, expected_total_tax=None, expected_chargeable_income=None, **kwargs):
    """TRL reward function: exact final total (1.0) or exact CI (0.25)."""
    rewards = []
    expected_tax = expected_total_tax or [None] * len(completions)
    expected_ci = expected_chargeable_income or [None] * len(completions)
    for completion, want_tax, want_ci in zip(completions, expected_tax, expected_ci):
        text = completion or ""
        reward = 0.0
        if want_tax is not None:
            predicted = extract_labeled_amount(text, TOTAL_TAX_RE)
            if predicted is not None and predicted == norm_amount(str(want_tax)):
                reward = 1.0
            elif want_ci:
                predicted_ci = extract_labeled_amount(text, CHARGEABLE_INCOME_RE)
                if predicted_ci is not None and predicted_ci == norm_amount(str(want_ci)):
                    reward = 0.25
        rewards.append(reward)
    return rewards


def reward_check() -> None:
    cases = [
        ("Total tax: NGN 100.00.", "100.00", "800.00", 1.0, "exact total"),
        ("Chargeable income: NGN 800.00. Total tax: NGN 100.00.", "100.00", "800.00", 1.0, "exact total + CI"),
        ("Chargeable income: NGN 800.00. Total tax: NGN 999.00.", "100.00", "800.00", 0.25, "CI only"),
        ("Chargeable income: NGN 999.00. Total tax: NGN 999.00.", "100.00", "800.00", 0.0, "both wrong"),
        ("I need to know your salary first.", "100.00", "800.00", 0.0, "no total"),
    ]
    ok = True
    for completion, want_tax, want_ci, expected_reward, label in cases:
        got = tax_reward([completion], [want_tax], [want_ci])[0]
        status = "ok" if abs(got - expected_reward) < 1e-9 else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  [{status}] {label}: reward={got} (want {expected_reward})")
    if not ok:
        raise SystemExit("reward function self-test failed")


def check(args) -> None:
    rows = load_pool(args.pool)
    if not rows:
        raise SystemExit(f"pool empty or missing: {args.pool}")
    languages = {}
    tiers = {}
    for row in rows:
        languages[row.get("language", "en")] = languages.get(row.get("language", "en"), 0) + 1
        tiers[row.get("tier", "unknown")] = tiers.get(row.get("tier", "unknown"), 0) + 1
    print(f"pool: {len(rows)} prompts from {args.pool}")
    print(f"  languages: {languages}")
    print(f"  tiers: {tiers}")
    print("reward function self-test:")
    reward_check()
    print("dataset check: OK")


def disable_thinking(tokenizer) -> None:
    template = getattr(tokenizer, "chat_template", None)
    if not isinstance(template, str) or "enable_thinking" not in template:
        return
    if template.lstrip().startswith("{%- set enable_thinking"):
        return
    tokenizer.chat_template = "{%- set enable_thinking = false %}\n" + template


def build_dataset(rows: list[dict]):
    from datasets import Dataset

    records = []
    for row in rows:
        records.append({
            "prompt": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": row["prompt"]},
            ],
            "expected_total_tax": str(row["expected_total_tax"]),
            "expected_chargeable_income": str(row.get("expected_chargeable_income") or ""),
        })
    return Dataset.from_list(records)


def dry_run(args, rows: list[dict]) -> None:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    disable_thinking(tokenizer)
    lengths = []
    for row in rows:
        prompt_text = tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": row["prompt"]}],
            tokenize=False, add_generation_prompt=True,
        )
        lengths.append(len(tokenizer(prompt_text, add_special_tokens=False).input_ids))
    print(f"prompt tokens: min {min(lengths)} / avg {sum(lengths)//len(lengths)} / max {max(lengths)}")
    for row in rows[: args.dry_run]:
        prompt_text = tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": row["prompt"]}],
            tokenize=False, add_generation_prompt=True,
        )
        print("=" * 70)
        print(f"{row['id']} | tier={row['tier']} | expected total {row['expected_total_tax']}")
        print(prompt_text[-450:].replace("\n", " \\n "))
    print("dry run: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="unsloth/Qwen3-1.7B", help="KTO merged checkpoint")
    parser.add_argument("--pool", type=Path, default=ROOT / "data" / "grpo" / "train_pool.jsonl")
    parser.add_argument("--out", default=None)
    parser.add_argument("--epochs", type=float, default=1)
    parser.add_argument("--lr", type=float, default=1e-6)
    parser.add_argument("--beta", type=float, default=0.04)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--num-generations", type=int, default=8)
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--max-completion-length", type=int, default=320)
    parser.add_argument("--micro-batch", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lora-r", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--check", action="store_true", help="validate pool + reward only (no model)")
    parser.add_argument("--dry-run", type=int, default=0, metavar="N")
    args = parser.parse_args()

    if args.check:
        check(args)
        return

    rows = load_pool(args.pool)
    if not rows:
        raise SystemExit(f"pool empty or missing: {args.pool}")

    if args.dry_run:
        dry_run(args, rows)
        return

    if not args.out:
        raise SystemExit("--out is required for training")

    import torch
    from unsloth import FastLanguageModel
    try:
        from unsloth import PatchFastRL
        PatchFastRL("GRPO", FastLanguageModel)
    except ImportError:
        pass
    from trl import GRPOConfig, GRPOTrainer
    from datasets import Dataset

    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_prompt_length + args.max_completion_length,
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

    dataset = build_dataset(rows)
    print(f"train prompts: {len(dataset)} | num_generations {args.num_generations} "
          f"| generation batch {args.micro_batch * args.grad_accum}")

    config_kwargs = dict(
        output_dir=os.path.join(args.out, "checkpoints"),
        per_device_train_batch_size=args.micro_batch,
        gradient_accumulation_steps=args.grad_accum,
        num_generations=args.num_generations,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        beta=args.beta,
        temperature=args.temperature,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=5,
        save_strategy="epoch",
        optim="adamw_8bit",
        reward_weights=[1.0],
        seed=args.seed,
        report_to="none",
    )
    try:
        import inspect
        supported = set(inspect.signature(GRPOConfig.__init__).parameters)
        config_kwargs = {key: value for key, value in config_kwargs.items() if key in supported}
    except (TypeError, ValueError):
        pass
    config = GRPOConfig(**config_kwargs)
    print("GRPO config:", {key: value for key, value in config_kwargs.items() if key != "output_dir"})

    trainer_kwargs = dict(
        model=model,
        reward_funcs=[tax_reward],
        args=config,
        train_dataset=dataset,
    )
    try:
        trainer = GRPOTrainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError as exc:
        if "processing_class" not in str(exc):
            raise
        trainer = GRPOTrainer(tokenizer=tokenizer, **trainer_kwargs)

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
        "pool": str(args.pool),
        "prompts": len(dataset),
        "epochs": args.epochs,
        "lr": args.lr,
        "beta": args.beta,
        "temperature": args.temperature,
        "num_generations": args.num_generations,
        "max_completion_length": args.max_completion_length,
        "lora_r": args.lora_r,
        "training_loss": result.training_loss,
    }
    with open(os.path.join(args.out, "grpo_run.json"), "w") as fh:
        json.dump(metadata, fh, indent=2)
    print("run metadata ->", os.path.join(args.out, "grpo_run.json"))


if __name__ == "__main__":
    main()
