#!/usr/bin/env python3
"""Verify JSONL records against source scenarios and the deterministic engine."""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset


REQUIRED_FIELDS = {
    "id",
    "category",
    "language",
    "instruction",
    "output",
    "verified_by_engine",
    "verification",
    "source_fact_ids",
    "scenario_family",
    "generated_by",
    "human_reviewed",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def amount_in_text(value, text: str) -> bool:
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    if amount == amount.to_integral_value():
        formatted = f"{int(amount):,}"
        plain = str(int(amount))
    else:
        formatted = f"{amount:,.2f}"
        plain = f"{amount:g}"
    patterns = (
        rf"(?<!\d){re.escape(formatted)}(?!\d)",
        rf"(?<!\d){re.escape(plain)}(?!\d)",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def compare_number(actual, expected) -> bool:
    return Decimal(str(actual)) == Decimal(str(expected))


def verify_file(path: Path, scenario_map: dict[str, dict], ruleset: dict) -> list[str]:
    errors = []
    seen = set()
    for line_number, record in enumerate(read_jsonl(path), start=1):
        label = f"{path}:{line_number}"
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            errors.append(f"{label}: missing fields {sorted(missing)}")
            continue
        if record["id"] in seen:
            errors.append(f"{label}: duplicate id {record['id']}")
        seen.add(record["id"])
        if not record["instruction"].strip() or not record["output"].strip():
            errors.append(f"{label}: empty instruction or output")
        if len(record["output"].split()) > 350:
            errors.append(f"{label}: output exceeds 350 words")
        if not record["source_fact_ids"]:
            errors.append(f"{label}: no source_fact_ids")

        scenario_id = record.get("scenario_id")
        if not scenario_id:
            if record["verification"] != "source_register":
                errors.append(f"{label}: non-scenario record must use source_register verification")
            if record["ground_truth"] is not None:
                errors.append(f"{label}: source-only record must have null ground_truth")
            if not record["human_reviewed"] and not record.get("source_verified"):
                errors.append(f"{label}: source-only record must be source_verified or human_reviewed")
            continue

        scenario = scenario_map.get(scenario_id)
        if scenario is None:
            errors.append(f"{label}: unknown scenario_id {scenario_id}")
            continue
        if set(record["source_fact_ids"]) != set(scenario["source_fact_ids"]):
            errors.append(f"{label}: source_fact_ids differ from authoritative scenario")
        if record["scenario_family"] != scenario["scenario_family"]:
            errors.append(f"{label}: scenario_family differs from authoritative scenario")
        truth = record.get("ground_truth") or {}
        expected = scenario["ground_truth"]
        if record["category"] == "counterfactual":
            if truth != expected:
                errors.append(f"{label}: counterfactual ground_truth mismatch")
            base_result = calculate_full(
                truth["gross_annual_salary"],
                truth["base_relief_inputs"],
                ruleset,
            )
            scenario_reliefs = {
                **truth["base_relief_inputs"],
                truth["changed_field"]: truth["new_pension"],
            }
            scenario_result = calculate_full(
                truth["gross_annual_salary"], scenario_reliefs, ruleset
            )
            checks = (
                ("base_chargeable_income", base_result["chargeable_income"]),
                ("scenario_chargeable_income", scenario_result["chargeable_income"]),
                ("base_tax", base_result["total_tax"]),
                ("scenario_tax", scenario_result["total_tax"]),
                ("tax_saving", base_result["total_tax"] - scenario_result["total_tax"]),
            )
            for key, actual in checks:
                if not compare_number(actual, truth[key]):
                    errors.append(f"{label}: counterfactual engine mismatch for {key}")
                if not amount_in_text(truth[key], record["output"]):
                    errors.append(f"{label}: output omits counterfactual value {key}")
            if not record["verified_by_engine"] or record["verification"] != "engine":
                errors.append(f"{label}: counterfactual record must be engine-verified")
            continue
        for key in ("gross_annual_salary", "relief_inputs", "expected_chargeable_income", "expected_total_tax"):
            if truth.get(key) != expected.get(key):
                errors.append(f"{label}: ground_truth mismatch for {key}")
        result = calculate_full(truth["gross_annual_salary"], truth["relief_inputs"], ruleset)
        if not compare_number(result["chargeable_income"], truth["expected_chargeable_income"]):
            errors.append(f"{label}: engine chargeable-income mismatch")
        if not compare_number(result["total_tax"], truth["expected_total_tax"]):
            errors.append(f"{label}: engine tax mismatch")
        if not record["verified_by_engine"] or record["verification"] != "engine":
            errors.append(f"{label}: scenario record must be engine-verified")
        if not amount_in_text(truth["expected_chargeable_income"], record["output"]):
            errors.append(f"{label}: output omits expected chargeable income")
        if not amount_in_text(truth["expected_total_tax"], record["output"]):
            errors.append(f"{label}: output omits expected total tax")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--scenario-files", nargs="+", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenarios = {}
    family_by_file = {}
    for path in args.scenario_files:
        records = read_jsonl(path)
        family_by_file[path] = {record["scenario_family"] for record in records}
        scenarios.update({record["scenario_id"]: record for record in records})
    if len(args.files) == 2:
        first = set()
        second = set()
        for record in read_jsonl(args.files[0]):
            if record.get("scenario_family"):
                first.add(record["scenario_family"])
        for record in read_jsonl(args.files[1]):
            if record.get("scenario_family"):
                second.add(record["scenario_family"])
        overlap = first & second
        if overlap:
            raise SystemExit(f"scenario-family leakage between dataset files: {sorted(overlap)}")

    ruleset = load_ruleset()
    errors = []
    total = 0
    for path in args.files:
        total += len(read_jsonl(path))
        errors.extend(verify_file(path, scenarios, ruleset))
    if errors:
        print(f"FAILED: {len(errors)} errors across {total} records")
        print("\n".join(errors[:50]))
        raise SystemExit(1)
    print(f"PASS: verified {total} records")


if __name__ == "__main__":
    main()
