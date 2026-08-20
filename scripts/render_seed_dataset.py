#!/usr/bin/env python3
"""Render deterministic scenarios and verified source facts as JSONL Q&A data."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

 

RELIEF_OUTPUT_LABELS = {
    "rent": "rent relief",
    "pension": "pension contribution",
    "nhf": "NHF contribution",
    "nhis": "NHIS contribution",
    "mortgage_interest": "mortgage-interest deduction",
    "life_insurance": "life-insurance deduction",
}


def money(value) -> str:
    rounded = Decimal(str(value)).quantize(Decimal("0.01"))
    if rounded == rounded.to_integral_value():
        return f"NGN {int(rounded):,}"
    return f"NGN {rounded:,.2f}"


def shorthand_money(value) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    million = Decimal("1000000")
    thousand = Decimal("1000")
    if amount >= million and amount % Decimal("100000") == 0:
        number = format(amount / million, "f").rstrip("0").rstrip(".")
        return f"{number}m"
    if amount >= thousand and amount % thousand == 0:
        number = format(amount / thousand, "f").rstrip("0").rstrip(".")
        return f"{number}k"
    return money(amount)


def percentage(rate) -> str:
    number = format(Decimal(str(rate)) * 100, "f").rstrip("0").rstrip(".")
    return f"{number}%"


def relief_facts(record: dict, shorthand: bool = False) -> str:
    parts = []
    for relief_id, amount in record["relief_inputs"].items():
        amount_text = shorthand_money(amount) if shorthand else money(amount)
        if relief_id == "rent":
            parts.append(f"I pay {amount_text} in rent")
        elif relief_id == "pension":
            parts.append(f"I contribute {amount_text} to pension")
        elif relief_id == "nhf":
            parts.append(f"my NHF contribution is {amount_text}")
        elif relief_id == "nhis":
            parts.append(f"my NHIS contribution is {amount_text}")
        elif relief_id == "mortgage_interest":
            parts.append(f"I pay {amount_text} in mortgage interest")
        else:
            parts.append(f"my life-insurance premium is {amount_text}")
    if not parts:
        return "no deductions or reliefs"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def salary_phrase(record: dict, shorthand: bool = False) -> str:
    presentation = record["presentation"]
    amount = shorthand_money(presentation["salary_amount"]) if shorthand else money(presentation["salary_amount"])
    if presentation["salary_period"] == "monthly":
        return f"{amount} every month"
    return f"{amount} a year"


def question_variants(record: dict) -> list[str]:
    facts = relief_facts(record)
    shorthand_facts = relief_facts(record, shorthand=True)
    return [
        f"I earn {salary_phrase(record)} and {facts}. How much tax do I pay? Please show the calculation.",
        f"For Nigeria's 2026 tax rules, I earn {salary_phrase(record)} and {facts}. What tax do I pay?",
        f"I earn {salary_phrase(record, shorthand=True)} and {shorthand_facts}. How much tax will I pay?",
    ]


def answer_text(record: dict, variant: int) -> str:
    truth = record["ground_truth"]
    scope_preamble = {
        1: "Assuming Nigeria and the 2026 year of assessment, based on the facts stated",
        2: "For Nigeria's 2026 rules, based on the facts stated",
        3: "I am treating this as a Nigeria 2026 calculation based on the facts stated",
    }[variant]
    lines = [
        f"{scope_preamble}. This is an estimate under the Nigeria Tax Act 2025.",
    ]
    if record["presentation"]["salary_period"] == "monthly":
        monthly = Decimal(str(truth["gross_annual_salary"])) / Decimal("12")
        lines.append(
            f"Monthly income: {money(monthly)} x 12 = gross annual income {money(truth['gross_annual_salary'])}."
        )
    else:
        lines.append(f"Gross annual income: {money(truth['gross_annual_salary'])}.")
    if truth["applied_reliefs"]:
        deductions = ", ".join(
            f"{RELIEF_OUTPUT_LABELS[key]} of {money(value)}"
            for key, value in truth["applied_reliefs"].items()
        )
        lines.append(f"Deductions applied: {deductions}.")
    else:
        lines.append("No deductions were applied from the facts provided.")
    lines.append(f"Chargeable income: {money(truth['expected_chargeable_income'])}.")
    taxed_bands = [
        f"{money(item['taxed_amount'])} at {percentage(item['rate'])} = {money(item['tax'])}"
        for item in truth["tax_breakdown"]
    ]
    if taxed_bands:
        lines.append("Band calculation: " + "; ".join(taxed_bands) + ".")
    lines.append(f"Estimated annual tax: {money(truth['expected_total_tax'])}.")
    lines.append(
        "Claims may require documentary evidence under section 32. "
        "Relevant sources are sections 30(1), 30(2)(a), 32, and the Fourth Schedule."
    )
    return " ".join(lines)


def static_facts() -> list[dict]:
    return [
        {
            "id": "fact-f001-bands",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "What are the individual income-tax bands in Nigeria for the 2026 year of assessment?",
            "output": (
                "Under the Fourth Schedule to the Nigeria Tax Act 2025, the bands are: first NGN 800,000 at 0%; "
                "next NGN 2,200,000 at 15%; next NGN 9,000,000 at 18%; next NGN 13,000,000 at 21%; "
                "next NGN 25,000,000 at 23%; and amounts above NGN 50,000,000 at 25%."
            ),
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-001"],
            "scenario_family": "fact_f001",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-f001-zero-band",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "What rate applies to the first NGN 800,000 of individual chargeable income in 2026?",
            "output": "The first NGN 800,000 of individual chargeable income is taxed at 0% under the Fourth Schedule to the Nigeria Tax Act 2025.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-001"],
            "scenario_family": "fact_f001",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-f004-rent",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "How is rent relief calculated under Nigeria's 2026 tax rules?",
            "output": "Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The individual must accurately declare the actual rent and other required information. The claim may require evidence under section 32.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-004", "F-005"],
            "scenario_family": "fact_f004",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-f003-deductions",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "Which individual payments are listed as eligible deductions under section 30 of the Nigeria Tax Act 2025?",
            "output": "The listed categories include NHF, NHIS, and Pension Reform Act contributions; interest on a loan for developing an owner-occupied residential house; qualifying life-insurance or deferred-annuity premiums; and rent relief. The claim must be made in the prescribed manner and may require documentary evidence.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-003", "F-005"],
            "scenario_family": "fact_f003",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-f005-proof",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "Can the tax authority ask for proof of a deduction claim?",
            "output": "Yes. Under section 32, the relevant tax authority may require documentary evidence for a deduction claim and may refuse or reduce the deduction if the evidence is absent or inadequate.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-005"],
            "scenario_family": "fact_f005",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-f006-nhf",
            "category": "statutory_fact",
            "language": "en",
            "instruction": "Is NHF contribution voluntary for private-sector employees?",
            "output": "The private-sector position is voluntary: the NHF Act 1992, as amended by section 45 of the Business Facilitation (Miscellaneous Provisions) Act 2022, uses 'may contribute' for private-sector employees. NHF contributions are separately listed as an eligible deduction under section 30(2)(a)(i) of the Nigeria Tax Act 2025. Confirm individual employment circumstances before relying on this treatment.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-006", "F-003"],
            "scenario_family": "fact_f006",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-scope-default",
            "category": "scope_behavior",
            "language": "en",
            "instruction": "I did not mention a country or tax year. What will you assume?",
            "output": "I default to Nigeria and the 2026 year of assessment. If you mean another country or year, say so; I only support Nigerian 2026 personal-income-tax questions in this version.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "scope_behavior",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-scope-country",
            "category": "scope_behavior",
            "language": "en",
            "instruction": "Calculate my Ghana personal income tax for 2026.",
            "output": "I cannot calculate Ghanaian tax. This version is scoped to Nigerian personal income tax for the 2026 year of assessment.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "scope_behavior",
            "generated_by": "manual",
            "human_reviewed": True,
        },
        {
            "id": "fact-scope-year",
            "category": "scope_behavior",
            "language": "en",
            "instruction": "Calculate my Nigerian personal income tax for 2025.",
            "output": "I cannot reliably calculate the 2025 rules in this version. I am scoped to Nigerian personal income tax for the 2026 year of assessment.",
            "ground_truth": None,
            "verified_by_engine": False,
            "verification": "source_register",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "scope_behavior",
            "generated_by": "manual",
            "human_reviewed": True,
        },
    ]


def render_record(scenario: dict, variant: int) -> dict:
    return {
        "id": f"{scenario['scenario_id']}-v{variant}",
        "scenario_id": scenario["scenario_id"],
        "category": scenario["category"],
        "language": "en",
        "instruction": question_variants(scenario)[variant - 1],
        "output": answer_text(scenario, variant),
        "ground_truth": copy.deepcopy(scenario["ground_truth"]),
        "verified_by_engine": True,
        "verification": "engine",
        "source_fact_ids": scenario["source_fact_ids"],
        "scenario_family": scenario["scenario_family"],
        "generated_by": "deterministic_template",
        "human_reviewed": False,
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-dir", type=Path, default=ROOT / "data" / "scenarios")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--variants", type=int, default=3, choices=(1, 2, 3))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_scenarios = read_jsonl(args.scenario_dir / "train.jsonl")
    eval_scenarios = read_jsonl(args.scenario_dir / "eval.jsonl")
    normalization_path = args.scenario_dir / "normalization.jsonl"
    normalization_scenarios = read_jsonl(normalization_path) if normalization_path.exists() else []
    train_records = static_facts()
    for scenario in train_scenarios + normalization_scenarios:
        train_records.extend(render_record(scenario, variant) for variant in range(1, args.variants + 1))
    eval_records = []
    for scenario in eval_scenarios:
        eval_records.append(render_record(scenario, 1))
    write_jsonl(args.output_dir / "train" / "seed.jsonl", train_records)
    write_jsonl(args.output_dir / "eval" / "seed.jsonl", eval_records)
    print(f"wrote {len(train_records)} training records")
    print(f"wrote {len(eval_records)} evaluation records")


if __name__ == "__main__":
    main()
