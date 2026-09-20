#!/usr/bin/env python3
"""Assemble the final SFT dataset from verified layers + replay.

Steps:
  1. Load all verified layers and the replay file.
  2. Deduplicate by normalized first user message.
  3. Guard: no SFT prompt may appear in any eval suite (paraphrase, coach,
     multi-turn, held-out probe, baseline prompts).
  4. Shuffle (seed 42) and split 95/5 into train/val.
  5. Write data/sft_v1/{train,val}.jsonl + MANIFEST.md with provenance.

Usage:
    uv run python scripts/assemble_sft_dataset.py
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERIFIED = ROOT / "data" / "sft_verified"
DEFAULT_OUT = ROOT / "data" / "sft_v1"

LAYERS = ["layer_a", "layer_b", "layer_c", "single_en", "single_pcm", "topup_v3"]
REPLAY = ROOT / "data" / "sft_generated" / "replay_en.jsonl"

EVAL_FILES = [
    "data/eval/paraphrase_suite.jsonl",
    "data/eval/coach_eval.jsonl",
    "data/eval/multiturn_suite.jsonl",
    "data/eval/probe_prompts_heldout.jsonl",
    "data/eval/baseline_prompts.jsonl",
]


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def user_texts(record: dict) -> list[str]:
    return [turn["content"] for turn in record.get("turns", []) if turn.get("role") == "user"]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-dir", type=Path, default=DEFAULT_VERIFIED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--label", default="SFT Dataset v1")
    args = parser.parse_args()
    VERIFIED = args.verified_dir.resolve()
    OUT = args.out.resolve()
    label = args.label

    records: list[tuple[str, dict]] = []
    for layer in LAYERS:
        path = VERIFIED / f"{layer}.jsonl"
        for record in load_jsonl(path):
            records.append((layer, record))
    for record in load_jsonl(REPLAY):
        records.append(("replay", record))

    print(f"loaded {len(records)} records")

    # dedupe by normalized full user-turn sequence
    seen: set[str] = set()
    deduped: list[tuple[str, dict]] = []
    duplicates = 0
    for source, record in records:
        texts = user_texts(record)
        key = " | ".join(norm(text) for text in texts) if texts else record["id"]
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append((source, record))
    print(f"deduplicated: removed {duplicates}, kept {len(deduped)}")

    # eval overlap guard
    eval_prompts: set[str] = set()
    for rel in EVAL_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        for row in load_jsonl(path):
            for field in ("prompt", "instruction"):
                if row.get(field):
                    eval_prompts.add(norm(row[field]))
            for turn in row.get("turns", []):
                if isinstance(turn, dict) and turn.get("user"):
                    eval_prompts.add(norm(turn["user"]))
    overlaps = []
    for source, record in deduped:
        for text in user_texts(record):
            if norm(text) in eval_prompts:
                overlaps.append((source, record["id"], text[:80]))
    if overlaps:
        print(f"FAIL: {len(overlaps)} eval overlaps, e.g. {overlaps[:3]}")
        raise SystemExit(1)
    print("eval overlap guard: clean")

    # shuffle + split
    rng = random.Random(42)
    rng.shuffle(deduped)
    val_size = max(1, int(len(deduped) * 0.05))
    val = deduped[:val_size]
    train = deduped[val_size:]

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("val", val)):
        with open(OUT / f"{name}.jsonl", "w") as fh:
            for _, record in rows:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    # manifest
    source_counts = Counter(source for source, _ in deduped)
    train_counts = Counter(source for source, _ in train)
    val_counts = Counter(source for source, _ in val)
    words = sum(
        len(turn["content"].split())
        for _, record in deduped
        for turn in record.get("turns", [])
        if turn.get("role") == "assistant"
    )
    lines = [
        "# {label} — Manifest",
        "",
        f"- Assembled: 2026-09-20 from verified layers + OASST1 replay",
        f"- Total examples: {len(deduped)} (train {len(train)} / val {len(val)})",
        f"- Assistant words (core+replay): {words:,}",
        f"- Duplicates removed: {duplicates}",
        f"- Eval overlap: none",
        "",
        "| Source | Total | Train | Val | File | sha256 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for layer in LAYERS + ["replay"]:
        path = (
            VERIFIED / f"{layer}.jsonl"
            if layer != "replay"
            else REPLAY
        )
        lines.append(
            f"| {layer} | {source_counts.get(layer, 0)} | {train_counts.get(layer, 0)} | "
            f"{val_counts.get(layer, 0)} | `{path.relative_to(ROOT)}` | {sha256(path)} |"
        )
    lines += [
        "",
        "Replay share: "
        + f"{source_counts.get('replay', 0) / max(len(deduped), 1):.1%} of examples "
        + f"({sum(1 for s, _ in deduped if s == 'replay')} OASST1 general-chat conversations)",
        "",
        "Answer format: headline first (total tax / saving / citation), then the working.",
    ]
    (OUT / "MANIFEST.md").write_text("\n".join(lines).replace("{label}", label) + "\n")
    print(f"wrote train={len(train)} val={len(val)} -> {OUT}")
    print("manifest ->", OUT / "MANIFEST.md")


if __name__ == "__main__":
    main()
