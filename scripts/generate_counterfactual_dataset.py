#!/usr/bin/env python3
"""Generate verified what-if pension scenarios from existing tax scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset

MONEY_PLACES = Decimal("0.01")


def decimal_string(value) -> str:
    return format(Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP), "f")


def money(value) -> str:
    amount = Decimal(str(value)).quantize(MONEY_PLACES)
    if amount == amount.to_integral_value():
        return f"NGN {int(amount):,}"
    return f"NGN {amount:,.2f}"


def shorthand(value) -> str:
    amount = Decimal(str(value)).quantize(MONEY_PLACES)
    if amount >= Decimal("1000000") and amount % Decimal("100000") == 0:
        return f"{format(amount / Decimal('1000000'), 'f').rstrip('0').rstrip('.')}m"
    if amount >= Decimal("1000") and amount % Decimal("1000") == 0:
        return f"{format(amount / Decimal('1000'), 'f').rstrip('0').rstrip('.')}k"
    return money(amount)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records))


def build_pair(index: int, split: str, base: dict, ruleset: dict) -> tuple[dict, dict]:
    truth = base["ground_truth"]
    base_reliefs = dict(truth["relief_inputs"])
    old_pension = Decimal(base_reliefs.get("pension", "0.00"))
    new_pension = old_pension + Decimal("120000.00")
    scenario_reliefs = {**base_reliefs, "pension": decimal_string(new_pension)}
    base_result = calculate_full(truth["gross_annual_salary"], base_reliefs, ruleset)
    scenario_result = calculate_full(truth["gross_annual_salary"], scenario_reliefs, ruleset)
    source_ids = list(base["source_fact_ids"])
    if "F-003" not in source_ids:
        source_ids.append("F-003")
    scenario_id = f"cf-{split}-{index:04d}"
    ground_truth = {
        "gross_annual_salary": truth["gross_annual_salary"],
        "base_relief_inputs": base_reliefs,
        "changed_field": "pension",
        "new_pension": decimal_string(new_pension),
        "base_chargeable_income": decimal_string(base_result["chargeable_income"]),
        "scenario_chargeable_income": decimal_string(scenario_result["chargeable_income"]),
        "base_tax": decimal_string(base_result["total_tax"]),
        "scenario_tax": decimal_string(scenario_result["total_tax"]),
        "tax_saving": decimal_string(base_result["total_tax"] - scenario_result["total_tax"]),
    }
    base_salary = base["presentation"]["salary_amount"]
    salary = shorthand(base_salary) if index % 2 else money(base_salary)
    context = "For Nigeria's 2026 rules, " if index % 3 == 0 else ""
    question = (
        f"{context}I earn {salary} {('every month' if base['presentation']['salary_period'] == 'monthly' else 'a year')} "
        f"and my current pension contribution is {shorthand(old_pension)}. "
        f"What if I increase it to {shorthand(new_pension)}? How would my tax change?"
    )
    output = (
        "Assuming Nigeria and the 2026 year of assessment, based on the stated facts: "
        f"current chargeable income is {money(base_result['chargeable_income'])} and current estimated tax is {money(base_result['total_tax'])}. "
        f"With pension contribution increased to {money(new_pension)}, chargeable income becomes {money(scenario_result['chargeable_income'])} "
        f"and estimated tax becomes {money(scenario_result['total_tax'])}. "
        f"Estimated tax saving: {money(base_result['total_tax'] - scenario_result['total_tax'])}. "
        "Pension contributions are listed under section 30(2)(a)(iii); documentary evidence may be required under section 32."
    )
    scenario = {
        "scenario_id": scenario_id,
        "split": split,
        "category": "counterfactual",
        "scenario_family": f"counterfactual-{split}-{base['scenario_family']}",
        "source_fact_ids": source_ids,
        "ground_truth": ground_truth,
    }
    record = {
        "id": f"{scenario_id}-v1",
        "scenario_id": scenario_id,
        "category": "counterfactual",
        "language": "en",
        "instruction": question,
        "output": output,
        "ground_truth": ground_truth,
        "verified_by_engine": True,
        "verification": "engine",
        "source_fact_ids": source_ids,
        "scenario_family": scenario["scenario_family"],
        "generated_by": "deterministic_template",
        "human_reviewed": False,
    }
    return scenario, record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--eval-count", type=int, default=16)
    args = parser.parse_args()
    ruleset = load_ruleset()
    bases = read_jsonl(ROOT / "data/scenarios/train.jsonl")
    train_scenarios = []
    train_records = []
    eval_scenarios = []
    eval_records = []
    for index in range(args.count):
        scenario, record = build_pair(index, "train", bases[index % len(bases)], ruleset)
        train_scenarios.append(scenario)
        train_records.append(record)
    for index in range(args.eval_count):
        base = bases[(args.count + index) % len(bases)]
        scenario, record = build_pair(index, "eval", base, ruleset)
        eval_scenarios.append(scenario)
        eval_records.append(record)
    write_jsonl(ROOT / "data/scenarios/counterfactual_train.jsonl", train_scenarios)
    write_jsonl(ROOT / "data/scenarios/counterfactual_eval.jsonl", eval_scenarios)
    write_jsonl(ROOT / "data/train/counterfactual.jsonl", train_records)
    write_jsonl(ROOT / "data/eval/counterfactual.jsonl", eval_records)
    print(f"wrote {len(train_records)} training counterfactuals")
    print(f"wrote {len(eval_records)} evaluation counterfactuals")


if __name__ == "__main__":
    main()
