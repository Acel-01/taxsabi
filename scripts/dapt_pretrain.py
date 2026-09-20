#!/usr/bin/env python3
"""DAPT — Domain-Adaptive Continued Pretraining (Unsloth QLoRA) for Qwen3-1.7B.

Continues next-token pretraining on the verified tax corpus with a replay mix
of general-domain text, then saves adapter + merged weights (and optionally
GGUF). Designed to run on T4 (16 GB) or AGH GPUs.

Corpus: every .txt under data/dapt_corpus plus the .md prose under
data/dapt_corpus/procedural (README files excluded).

Example:
    python scripts/dapt_pretrain.py \
        --out /content/models/dapt_qwen3_1.7b \
        --epochs 2 --lr 5e-5 --replay-ratio 0.15

Replay source options:
    --replay-dataset Salesforce/wikitext   (streams wikitext-103-raw-v1)
    --replay-file path/to/text.txt         (local general text)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_corpus(corpus_dir: Path) -> list[tuple[str, str]]:
    """Return [(name, text)] for corpus files; READMEs excluded."""
    files: list[Path] = []
    files += sorted(corpus_dir.glob("*.txt"))
    files += sorted((corpus_dir / "procedural").glob("*.md")) if (corpus_dir / "procedural").exists() else []
    documents = []
    for path in files:
        if path.name.lower().startswith("readme"):
            continue
        text = path.read_text()
        if text.strip():
            documents.append((str(path.relative_to(corpus_dir)), text))
    return documents


def load_replay_text(args, target_chars: int) -> str:
    if args.replay_file:
        text = Path(args.replay_file).read_text()
        return text[:target_chars]
    from datasets import load_dataset

    stream = load_dataset(args.replay_dataset, "wikitext-103-raw-v1", split="train", streaming=True)
    chunks: list[str] = []
    total = 0
    for row in stream:
        line = row["text"].strip()
        if len(line) < 80:  # skip headings and blanks
            continue
        chunks.append(line)
        total += len(line) + 1
        if total >= target_chars:
            break
    return "\n".join(chunks)


def make_cache_writable() -> None:
    """Unsloth's merge copies base weights from the HF cache; recent hub
    versions store cache files read-only, which makes the in-place merge fail.
    Make them writable before saving."""
    cache_root = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    if cache_root.exists():
        subprocess.run(["chmod", "-R", "u+w", str(cache_root)], check=False, capture_output=True)


def save_merged(model, tokenizer, merged_dir: str) -> bool:
    """Save the merged fp16 model without crashing the run if merging fails."""
    make_cache_writable()
    try:
        if not hasattr(model, "save_pretrained_merged"):
            raise AttributeError("save_pretrained_merged not available")
        model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")
        print("merged model saved to", merged_dir)
        return True
    except Exception as error:  # noqa: BLE001
        print(f"save_pretrained_merged failed ({type(error).__name__}: {error})")
    try:
        print("falling back to in-memory merge_and_unload ...")
        merged = model.merge_and_unload()
        merged.save_pretrained(merged_dir)
        tokenizer.save_pretrained(merged_dir)
        print("merged model saved to", merged_dir)
        return True
    except Exception as error:  # noqa: BLE001
        print(f"merge fallback failed too ({type(error).__name__}: {error})")
        print("adapter is saved and usable; merge later with scripts/merge_adapter.py")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="unsloth/Qwen3-1.7B")
    parser.add_argument("--corpus-dir", type=Path, default=ROOT / "data" / "dapt_corpus")
    parser.add_argument("--out", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--micro-batch", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lora-r", type=int, default=32)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--replay-ratio", type=float, default=0.15)
    parser.add_argument("--replay-dataset", default="Salesforce/wikitext")
    parser.add_argument("--replay-file", default=None)
    parser.add_argument("--val-fraction", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gguf", action="store_true", help="also export q4_k_m GGUF (slow)")
    args = parser.parse_args()

    import torch
    # Unsloth must be imported before transformers/trl so its patches apply.
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from datasets import Dataset
    from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    print("=== corpus ===")
    documents = read_corpus(args.corpus_dir)
    corpus_chars = sum(len(text) for _, text in documents)
    for name, text in documents:
        print(f"  {name}: {len(text):,} chars")
    print(f"  total: {corpus_chars:,} chars (~{corpus_chars // 4:,} tokens)")

    replay_chars = int(corpus_chars * args.replay_ratio)
    replay_text = load_replay_text(args, replay_chars)
    print(f"replay: {len(replay_text):,} chars ({args.replay_ratio:.0%} of corpus)")

    print("\n=== model ===")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_len,
        dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    print("\n=== tokenize + pack ===")
    texts = [text for _, text in documents] + [replay_text]
    dataset = Dataset.from_dict({"text": texts})

    def tokenize(batch):
        encoded = tokenizer(batch["text"], add_special_tokens=False)
        # separate documents with EOS so packing does not fuse them silently
        return {"input_ids": [ids + [tokenizer.eos_token_id] for ids in encoded["input_ids"]]}

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
    block = args.max_seq_len

    def group_texts(examples):
        concatenated: list[int] = []
        for ids in examples["input_ids"]:
            concatenated.extend(ids)
        total = (len(concatenated) // block) * block
        blocks = [concatenated[i : i + block] for i in range(0, total, block)]
        return {"input_ids": blocks, "labels": [list(ids) for ids in blocks]}

    packed = tokenized.map(group_texts, batched=True)
    split = packed.train_test_split(test_size=args.val_fraction, seed=args.seed)
    train_ds, val_ds = split["train"], split["test"]
    print(f"train blocks: {len(train_ds):,} | val blocks: {len(val_ds):,} | block size: {block}")

    print("\n=== training ===")
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    use_fp16 = not is_bfloat16_supported()
    trainer = Trainer(
        model=model,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        args=TrainingArguments(
            output_dir=os.path.join(args.out, "checkpoints"),
            per_device_train_batch_size=args.micro_batch,
            gradient_accumulation_steps=args.grad_accum,
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            report_to="none",
            seed=args.seed,
            fp16=use_fp16,
            bf16=not use_fp16,
        ),
    )
    started = time.time()
    result = trainer.train()
    elapsed = time.time() - started
    print(f"training_loss: {result.training_loss:.4f} | {elapsed / 60:.1f} min")

    model.save_pretrained(os.path.join(args.out, "adapter"))
    tokenizer.save_pretrained(os.path.join(args.out, "adapter"))

    merged_dir = os.path.join(args.out, "merged")
    merged_saved = save_merged(model, tokenizer, merged_dir)

    if args.gguf:
        try:
            model.save_pretrained_gguf(
                os.path.join(args.out, "gguf"), tokenizer, quantization_method="q4_k_m"
            )
            print("GGUF saved under", os.path.join(args.out, "gguf"))
        except Exception as error:  # noqa: BLE001
            print(f"GGUF export skipped ({type(error).__name__}: {error})")

    metadata = {
        "model": args.model,
        "corpus": {name: len(text) for name, text in documents},
        "corpus_chars": corpus_chars,
        "replay_chars": len(replay_text),
        "replay_ratio": args.replay_ratio,
        "train_blocks": len(train_ds),
        "val_blocks": len(val_ds),
        "block_size": block,
        "epochs": args.epochs,
        "lr": args.lr,
        "training_loss": result.training_loss,
        "minutes": round(elapsed / 60, 1),
        "merged_saved": merged_saved,
    }
    (Path(args.out) / "dapt_run.json").write_text(json.dumps(metadata, indent=2))
    print("run metadata ->", Path(args.out) / "dapt_run.json")


if __name__ == "__main__":
    main()
