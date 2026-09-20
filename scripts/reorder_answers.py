#!/usr/bin/env python3
"""Reorder calculation answers: move the headline total/saving to the END.

Verified data has the headline first ("Total tax: NGN X. Gross income: ...").
Small-model evidence shows the leading total is guessed while the band working
is computed, so the two contradict. This script deterministically rewrites the
order without touching any numbers:

    "Total tax: NGN 141,000. Gross income: ... bands ..."
      -> "Gross income: ... bands ... Total tax: NGN 141,000."

Same for "Saving" (counterfactual/coaching) and the Pidgin variants ("na").

Output: data/sft_verified_v2/<layer>.jsonl
Recheck: validates transformed records against the job blueprints.

Usage:
    uv run python scripts/reorder_answers.py
    uv run python scripts/reorder_answers.py --recheck
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

LAYERS = ["layer_a", "layer_b", "layer_c", "single_en", "single_pcm"]
IN_DIR = ROOT / "data" / "sft_verified"
OUT_DIR = ROOT / "data" / "sft_verified_v2"

HEADLINE_RE = re.compile(
    r"^(Total tax|Saving)(?P<na>\sna)?:?\s+(?P<amount>(?:NGN|\u20a6)\s?[\d,]+)\.\s+(?P<rest>.+)$",
    re.DOTALL,
)
AMOUNT_TOKEN = r"(?:NGN|\u20a6)\s?[\d,]+"


def reorder(text: str) -> str | None:
    """Return reordered text, or None when the pattern does not apply cleanly."""
    match = HEADLINE_RE.match(text.strip())
    if not match:
        return None
    label = match.group(1)
    amount = match.group("amount")
    rest = match.group("rest").rstrip()
    # skip when the rest already restates the same headline (avoid duplicates)
    if re.search(rf"\b{label}\b", rest):
        return None
    if not rest.endswith((".", "!", "?")):
        rest += "."
    if match.group("na"):
        return f"{rest} {label} na {amount}."
    return f"{rest} {label}: {amount}."


def transform_layer(layer: str) -> dict:
    src = IN_DIR / f"{layer}.jsonl"
    rows = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    transformed = 0
    skipped: list[tuple[str, str]] = []
    for row in rows:
        for i, turn in enumerate(row.get("turns", [])):
            if turn.get("role") != "assistant":
                continue
            new = reorder(turn["content"])
            if new is not None:
                turn["content"] = new
                transformed += 1
            elif re.match(r"^(Total tax|Saving)", turn["content"].strip()):
                skipped.append((row["id"], turn["content"][:80]))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / f"{layer}.jsonl", "w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"rows": len(rows), "transformed": transformed, "skipped": skipped}


def recheck() -> int:
    from verify_sft_generation import load_blueprints, verify_conversation  # noqa: E402

    language_map = {
        "layer_a": "en", "layer_b": "en", "layer_c": "pcm",
        "single_en": "en", "single_pcm": "pcm",
    }
    failures = 0
    for layer in LAYERS:
        blueprints = load_blueprints(layer)
        path = OUT_DIR / f"{layer}.jsonl"
        if not path.exists():
            print(f"{layer}: missing {path}")
            failures += 1
            continue
        bad = 0
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            blueprint = blueprints.get(record["id"])
            if blueprint is None:
                bad += 1
                continue
            ok, reasons = verify_conversation(record, blueprint, language_map[layer])
            if not ok:
                bad += 1
                print(f"  {record['id']}: {reasons[:2]}")
        status = "OK" if bad == 0 else f"{bad} FAILURES"
        print(f"{layer}: {status}")
        failures += bad
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recheck", action="store_true")
    args = parser.parse_args()

    if args.recheck:
        failures = recheck()
        print("recheck:", "clean" if failures == 0 else f"{failures} problems")
        raise SystemExit(1 if failures else 0)

    total_transformed = 0
    total_skipped = 0
    for layer in LAYERS:
        stats = transform_layer(layer)
        total_transformed += stats["transformed"]
        total_skipped += len(stats["skipped"])
        print(f"{layer}: {stats['rows']} records, {stats['transformed']} turns reordered, "
              f"{len(stats['skipped'])} skipped")
        for rid, preview in stats["skipped"][:3]:
            print(f"    skipped {rid}: {preview}")
    print(f"\ntotal turns reordered: {total_transformed} | skipped: {total_skipped}")
    print(f"output -> {OUT_DIR}")


if __name__ == "__main__":
    main()
