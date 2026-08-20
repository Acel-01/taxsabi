#!/usr/bin/env python3
"""Generate deterministic, engine-verified tax scenarios for dataset creation."""

from __future__ import annotations

import argparse
import json
import random
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import apply_relief, calculate_full, load_ruleset


TRAIN_FAMILIES = (
    "salary_only",
    "rent_below_cap",
    "rent_above_cap",
    "pension_only",
    "nhf_only",
    "nhis_only",
    "mortgage_only",
    "life_insurance_only",
    "rent_and_pension",
    "multiple_reliefs",
    "monthly_salary",
    "high_income",
)

EVAL_FAMILIES = (
    "below_zero_band",
    "at_zero_band",
    "above_zero_band",
    "at_second_band_edge",
    "rent_cap_edge",
    "monthly_band_edge",
    "high_income_edge",
    "relief_stack_edge",
)

MONEY_PLACES = Decimal("0.01")

SALARIES = (
    900_000,
    1_200_000,
    1_800_000,
    2_400_000,
    3_000_000,
    3_600_000,
    4_800_000,
    7_200_000,
    12_000_000,
    18_000_000,
    30_000_000,
)

NORMALIZATION_EXAMPLES = (
    (1_600_000, {"rent": 500_000}, {"salary_amount": 1_600_000, "salary_period": "annual", "input_style": "shorthand"}),
    (3_600_000, {}, {"salary_amount": 300_000, "salary_period": "monthly", "input_style": "shorthand"}),
    (7_200_000, {"rent": 300_000}, {"salary_amount": 7_200_000, "salary_period": "annual", "input_style": "shorthand"}),
    (4_800_000, {"rent": 3_000_000}, {"salary_amount": 4_800_000, "salary_period": "annual", "input_style": "shorthand"}),
    (12_000_000, {"pension": 240_000}, {"salary_amount": 1_000_000, "salary_period": "monthly", "input_style": "shorthand"}),
    (30_000_000, {"nhf": 60_000, "nhis": 72_000}, {"salary_amount": 30_000_000, "salary_period": "annual", "input_style": "shorthand"}),
)

RELIEF_FACTS = {
    "rent": "F-004",
    "pension": "F-003",
    "nhf": "F-003",
    "nhis": "F-003",
    "mortgage_interest": "F-003",
    "life_insurance": "F-003",
}


def choose_salary(rng: random.Random) -> int:
    return rng.choice(SALARIES)


def decimal_string(value) -> str:
    amount = Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
    return format(amount, "f")


def rate_string(value) -> str:
    return format(Decimal(str(value)).quantize(MONEY_PLACES), "f")


def make_inputs(family: str, rng: random.Random) -> tuple[int, dict[str, int], dict]:
    if family == "shorthand_money":
        return rng.choice(NORMALIZATION_EXAMPLES)
    if family == "below_zero_band":
        return 799_999, {}, {"salary_amount": 799_999, "salary_period": "annual"}
    if family == "at_zero_band":
        return 800_000, {}, {"salary_amount": 800_000, "salary_period": "annual"}
    if family == "above_zero_band":
        return 800_001, {}, {"salary_amount": 800_001, "salary_period": "annual"}
    if family == "at_second_band_edge":
        return 3_000_000, {}, {"salary_amount": 3_000_000, "salary_period": "annual"}
    if family == "rent_cap_edge":
        return 4_800_000, {"rent": 2_500_000}, {
            "salary_amount": 4_800_000,
            "salary_period": "annual",
        }
    if family == "monthly_band_edge":
        return 3_000_000, {}, {"salary_amount": 250_000, "salary_period": "monthly"}
    if family == "high_income_edge":
        return 50_000_001, {}, {"salary_amount": 50_000_001, "salary_period": "annual"}
    if family == "relief_stack_edge":
        return 2_000_000, {
            "rent": 2_500_000,
            "pension": 300_000,
        }, {"salary_amount": 2_000_000, "salary_period": "annual"}

    if family == "monthly_salary":
        monthly = rng.choice((100_000, 125_000, 150_000, 200_000, 300_000, 500_000))
        return monthly * 12, {}, {"salary_amount": monthly, "salary_period": "monthly"}

    salary = choose_salary(rng)
    if family == "salary_only":
        reliefs = {}
    elif family == "rent_below_cap":
        reliefs = {"rent": rng.choice((300_000, 600_000, 900_000, 1_200_000))}
    elif family == "rent_above_cap":
        reliefs = {"rent": rng.choice((2_500_000, 3_000_000, 5_000_000))}
    elif family == "pension_only":
        reliefs = {"pension": rng.choice((120_000, 240_000, 438_000, 600_000))}
    elif family == "nhf_only":
        reliefs = {"nhf": rng.choice((30_000, 60_000, 90_000, 120_000))}
    elif family == "nhis_only":
        reliefs = {"nhis": rng.choice((24_000, 48_000, 72_000))}
    elif family == "mortgage_only":
        reliefs = {"mortgage_interest": rng.choice((150_000, 300_000, 750_000))}
    elif family == "life_insurance_only":
        reliefs = {"life_insurance": rng.choice((100_000, 250_000, 500_000))}
    elif family == "rent_and_pension":
        reliefs = {
            "rent": rng.choice((600_000, 1_200_000, 2_500_000)),
            "pension": rng.choice((120_000, 240_000, 438_000)),
        }
    elif family == "multiple_reliefs":
        reliefs = {
            "rent": rng.choice((900_000, 1_800_000, 3_000_000)),
            "pension": rng.choice((120_000, 240_000, 480_000)),
            "nhf": rng.choice((30_000, 60_000)),
            "life_insurance": rng.choice((100_000, 250_000)),
        }
    elif family == "high_income":
        salary = rng.choice((12_000_000, 25_000_000, 50_000_000, 60_000_000, 100_000_000))
        reliefs = {"pension": rng.choice((240_000, 600_000, 1_200_000))}
    else:
        raise ValueError(f"unknown scenario family: {family}")

    return salary, reliefs, {"salary_amount": salary, "salary_period": "annual"}


def source_fact_ids(reliefs: dict[str, int]) -> list[str]:
    facts = ["F-001", "F-002", "F-005"]
    for relief_id in reliefs:
        fact_id = RELIEF_FACTS[relief_id]
        if fact_id not in facts:
            facts.append(fact_id)
        if relief_id == "rent" and "F-004" not in facts:
            facts.append("F-004")
    return facts


def build_scenario(
    index: int,
    split: str,
    family: str,
    rng: random.Random,
    ruleset: dict,
    forced_inputs=None,
) -> dict:
    gross, reliefs, presentation = forced_inputs or make_inputs(family, rng)
    result = calculate_full(gross, reliefs, ruleset)
    applied = {
        relief_id: apply_relief(relief_id, amount, ruleset)
        for relief_id, amount in reliefs.items()
    }
    wire_reliefs = {key: decimal_string(value) for key, value in reliefs.items()}
    wire_applied = {key: decimal_string(value) for key, value in applied.items()}
    wire_breakdown = [
        {
            "band": item["band"],
            "rate": rate_string(item["rate"]),
            "taxed_amount": decimal_string(item["taxed_amount"]),
            "tax": decimal_string(item["tax"]),
        }
        for item in result["breakdown"]
    ]
    return {
        "scenario_id": f"{split}-{index:04d}",
        "split": split,
        "category": "calculation",
        "scenario_family": family,
        "presentation": {
            "salary_amount": decimal_string(presentation["salary_amount"]),
            "salary_period": presentation["salary_period"],
            **({"input_style": presentation["input_style"]} if "input_style" in presentation else {}),
        },
        "relief_inputs": wire_reliefs,
        "source_fact_ids": source_fact_ids(reliefs),
        "ground_truth": {
            "gross_annual_salary": decimal_string(gross),
            "relief_inputs": wire_reliefs,
            "applied_reliefs": wire_applied,
            "total_relief": decimal_string(result["total_relief"]),
            "expected_chargeable_income": decimal_string(result["chargeable_income"]),
            "expected_total_tax": decimal_string(result["total_tax"]),
            "tax_breakdown": wire_breakdown,
        },
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-count", type=int, default=240)
    parser.add_argument("--eval-count", type=int, default=48)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "scenarios")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ruleset = load_ruleset()
    rng = random.Random(args.seed)
    train = [
        build_scenario(i, "train", TRAIN_FAMILIES[i % len(TRAIN_FAMILIES)], rng, ruleset)
        for i in range(args.train_count)
    ]
    evaluation = [
        build_scenario(i, "eval", EVAL_FAMILIES[i % len(EVAL_FAMILIES)], rng, ruleset)
        for i in range(args.eval_count)
    ]
    normalization = [
        build_scenario(
            i,
            "norm",
            "shorthand_money",
            rng,
            ruleset,
            forced_inputs=example,
        )
        for i, example in enumerate(NORMALIZATION_EXAMPLES)
    ]
    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "eval.jsonl", evaluation)
    write_jsonl(args.output_dir / "normalization.jsonl", normalization)
    print(f"wrote {len(train)} training scenarios to {args.output_dir / 'train.jsonl'}")
    print(f"wrote {len(evaluation)} eval scenarios to {args.output_dir / 'eval.jsonl'}")
    print(f"wrote {len(normalization)} normalization scenarios to {args.output_dir / 'normalization.jsonl'}")


if __name__ == "__main__":
    main()
