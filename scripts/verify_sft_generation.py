#!/usr/bin/env python3
"""Verify generated SFT conversations against the job blueprints.

Checks, per conversation:
  1. Schema: id matches a blueprint, turns alternate user/assistant starting
     with user, 3-8 turns, language matches the layer.
  2. Every amount the assistant states exists in the blueprint's authoritative
     values (engine-computed) or in the allowed tax constants.
  3. Required key figures appear: total tax (and saving where applicable).
  4. Required terms appear for fact/procedure blueprints.

Passing conversations are written to data/sft_verified/<layer>.jsonl with
verified_by_engine=true. Failures go to <layer>_rejected.jsonl with reasons.

Usage:
    uv run python scripts/verify_sft_generation.py --layer layer_a
    uv run python scripts/verify_sft_generation.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "data" / "sft_jobs"
GENERATED = ROOT / "data" / "sft_generated"
VERIFIED = ROOT / "data" / "sft_verified"

AMOUNT_RE = re.compile(r"(?:NGN|\u20a6|N(?=\d))\s*([\d][\d,]*(?:\.\d{1,2})?)", re.IGNORECASE)
BARE_AMOUNT_RE = re.compile(r"(?<![\d,.])(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)(?![\d,])")
BAND_NUMBER_RE = re.compile(r"\d[\d,]*")

# Thresholds and caps that may legitimately appear in any answer.
CONSTANTS = {
    Decimal("800000"), Decimal("2200000"), Decimal("3000000"),
    Decimal("9000000"), Decimal("12000000"), Decimal("13000000"),
    Decimal("25000000"), Decimal("50000000"), Decimal("500000"), Decimal("70000"),
}


def parse_decimal(text: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d.]", "", text)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def collect_values(obj, values: set[Decimal]) -> None:
    if isinstance(obj, dict):
        for value in obj.values():
            collect_values(value, values)
    elif isinstance(obj, list):
        for value in obj:
            collect_values(value, values)
    elif isinstance(obj, (str, int, float, Decimal)):
        if isinstance(obj, str):
            for match in BAND_NUMBER_RE.findall(obj):
                parsed = parse_decimal(match)
                if parsed is not None:
                    values.add(parsed)
        else:
            values.add(Decimal(str(obj)))


def allowed_values(blueprint: dict) -> set[Decimal]:
    values: set[Decimal] = set(CONSTANTS)
    collect_values(blueprint.get("authoritative", {}), values)
    return values


def extract_amounts(text: str) -> set[Decimal]:
    amounts = set()
    for pattern in (AMOUNT_RE, BARE_AMOUNT_RE):
        for match in pattern.findall(text):
            parsed = parse_decimal(match)
            if parsed is not None:
                amounts.add(parsed)
    return amounts


def amount_in_set(amount: Decimal, values: set[Decimal]) -> bool:
    return any(abs(amount - candidate) <= Decimal("1") for candidate in values)


def required_key_figures(blueprint: dict) -> list[Decimal]:
    """Key engine values that must appear in the assistant text."""
    auth = blueprint.get("authoritative", {})
    keys: list[Decimal] = []
    btype = blueprint.get("type", "")
    if btype == "counterfactual" or btype in ("coaching_discovery", "coaching_sequencing"):
        for key in ("scenario_tax", "tax_saving"):
            if auth.get(key):
                parsed = parse_decimal(str(auth[key]))
                if parsed is not None:
                    keys.append(parsed)
    elif btype == "coaching_savings":
        for key in ("scenario_tax", "tax_saving"):
            if auth.get(key):
                parsed = parse_decimal(str(auth[key]))
                if parsed is not None:
                    keys.append(parsed)
    elif btype == "correction":
        corrected = auth.get("corrected", {})
        if corrected.get("total_tax"):
            parsed = parse_decimal(str(corrected["total_tax"]))
            if parsed is not None:
                keys.append(parsed)
    else:
        if auth.get("total_tax"):
            parsed = parse_decimal(str(auth["total_tax"]))
            if parsed is not None:
                keys.append(parsed)
    return keys


def check_schema(conversation: dict, blueprint: dict, language: str) -> list[str]:
    problems = []
    if conversation.get("id") != blueprint["conversation_id"]:
        problems.append(f"id mismatch: {conversation.get('id')}")
    if conversation.get("language") != language:
        problems.append(f"language mismatch: {conversation.get('language')}")
    turns = conversation.get("turns")
    if not isinstance(turns, list) or not (3 <= len(turns) <= 8):
        problems.append(f"turn count invalid: {len(turns) if isinstance(turns, list) else 'missing'}")
        return problems
    roles = [turn.get("role") for turn in turns]
    expected = ["user" if i % 2 == 0 else "assistant" for i in range(len(turns))]
    if roles != expected:
        problems.append(f"role pattern invalid: {roles}")
    for i, turn in enumerate(turns):
        if not str(turn.get("content", "")).strip():
            problems.append(f"empty content in turn {i}")
    return problems


def verify_conversation(conversation: dict, blueprint: dict, language: str) -> tuple[bool, list[str]]:
    problems = check_schema(conversation, blueprint, language)
    if problems:
        return False, problems

    assistant_text = " ".join(
        turn["content"] for turn in conversation["turns"] if turn["role"] == "assistant"
    )
    amounts = extract_amounts(assistant_text)
    allowed = allowed_values(blueprint)
    bad = sorted(amount for amount in amounts if not amount_in_set(amount, allowed))
    if bad:
        problems.append("unauthorised amounts: " + ", ".join(str(value) for value in bad[:8]))

    for required in required_key_figures(blueprint):
        if not amount_in_set(required, amounts):
            problems.append(f"required figure missing: {required}")

    for term in blueprint.get("required_terms", []):
        if term.lower() not in assistant_text.lower():
            problems.append(f"required term missing: {term}")

    return not problems, problems


def load_blueprints(layer: str) -> dict[str, dict]:
    index = {}
    for path in sorted((JOBS / layer).glob("batch_*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                blueprint = json.loads(line)
                index[blueprint["conversation_id"]] = blueprint
    return index


def run_layer(layer: str) -> None:
    blueprints = load_blueprints(layer)
    language = {"layer_a": "en", "layer_b": "en", "layer_c": "pcm"}[layer]
    generated_dir = GENERATED / layer
    if not generated_dir.exists():
        print(f"{layer}: no generated files at {generated_dir} - skipping")
        return

    passed, rejected = [], []
    seen = set()
    for path in sorted(generated_dir.glob("batch_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                conversation = json.loads(line)
            except json.JSONDecodeError as error:
                rejected.append({"id": f"{path.name}:parse", "reasons": [f"invalid JSON: {error}"]})
                continue
            conv_id = conversation.get("id", "")
            seen.add(conv_id)
            blueprint = blueprints.get(conv_id)
            if blueprint is None:
                rejected.append({"id": conv_id, "reasons": ["no matching blueprint"]})
                continue
            ok, reasons = verify_conversation(conversation, blueprint, language)
            if ok:
                conversation["verified_by_engine"] = True
                conversation["verification"] = "engine+schema"
                conversation["engine_verified_at"] = datetime.now(timezone.utc).isoformat()
                passed.append(conversation)
            else:
                rejected.append({"id": conv_id, "reasons": reasons, "conversation": conversation})

    missing = sorted(set(blueprints) - seen)
    VERIFIED.mkdir(parents=True, exist_ok=True)
    with open(VERIFIED / f"{layer}.jsonl", "w") as fh:
        for conversation in passed:
            fh.write(json.dumps(conversation, ensure_ascii=False) + "\n")
    with open(VERIFIED / f"{layer}_rejected.jsonl", "w") as fh:
        for item in rejected:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"=== {layer} ===")
    print(f"blueprints: {len(blueprints)} | generated: {len(seen)} | verified: {len(passed)} | rejected: {len(rejected)}")
    if missing:
        print(f"not yet generated: {len(missing)}")
    reason_counts: dict[str, int] = {}
    for item in rejected:
        for reason in item["reasons"]:
            key = reason.split(":")[0]
            reason_counts[key] = reason_counts.get(key, 0) + 1
    for reason, count in sorted(reason_counts.items(), key=lambda kv: -kv[1])[:6]:
        print(f"  {reason}: {count}")
    print(f"verified -> {VERIFIED / f'{layer}.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", choices=["layer_a", "layer_b", "layer_c"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all:
        for layer in ("layer_a", "layer_b", "layer_c"):
            run_layer(layer)
    elif args.layer:
        run_layer(args.layer)
    else:
        parser.error("pass --layer or --all")


if __name__ == "__main__":
    main()
