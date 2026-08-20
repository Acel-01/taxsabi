#!/usr/bin/env python3
"""Generate targeted v6 records for the observed model failure modes."""

from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_scenarios import build_scenario
from render_seed_dataset import answer_text, money, percentage, question_variants
from rules_engine.engine import load_ruleset


TARGETS = [
    (799_998, {}, {"salary_amount": 799_998, "salary_period": "annual"}),
    (800_002, {}, {"salary_amount": 800_002, "salary_period": "annual"}),
    (2_999_999, {}, {"salary_amount": 2_999_999, "salary_period": "annual"}),
    (3_000_001, {}, {"salary_amount": 3_000_001, "salary_period": "annual"}),
    (11_999_999, {}, {"salary_amount": 11_999_999, "salary_period": "annual"}),
    (12_000_001, {}, {"salary_amount": 12_000_001, "salary_period": "annual"}),
    (24_999_999, {}, {"salary_amount": 24_999_999, "salary_period": "annual"}),
    (25_000_001, {}, {"salary_amount": 25_000_001, "salary_period": "annual"}),
    (49_999_999, {}, {"salary_amount": 49_999_999, "salary_period": "annual"}),
    (50_000_002, {}, {"salary_amount": 50_000_002, "salary_period": "annual"}),
    (1_500_000, {}, {"salary_amount": 125_000, "salary_period": "monthly"}),
    (2_400_000, {}, {"salary_amount": 200_000, "salary_period": "monthly"}),
    (3_600_000, {}, {"salary_amount": 300_000, "salary_period": "monthly"}),
    (6_000_000, {}, {"salary_amount": 500_000, "salary_period": "monthly"}),
    (1_500_000, {"rent": 1_200_000, "pension": 120_000}, {"salary_amount": 1_500_000, "salary_period": "annual"}),
    (4_800_000, {"rent": 2_499_000}, {"salary_amount": 4_800_000, "salary_period": "annual"}),
    (810_000, {}, {"salary_amount": 810_000, "salary_period": "annual"}),
    (2_990_000, {}, {"salary_amount": 2_990_000, "salary_period": "annual"}),
    (3_010_000, {}, {"salary_amount": 3_010_000, "salary_period": "annual"}),
    (12_100_000, {}, {"salary_amount": 12_100_000, "salary_period": "annual"}),
    (25_100_000, {}, {"salary_amount": 25_100_000, "salary_period": "annual"}),
    (50_100_000, {}, {"salary_amount": 50_100_000, "salary_period": "annual"}),
    (3_720_000, {}, {"salary_amount": 310_000, "salary_period": "monthly"}),
    (5_040_000, {}, {"salary_amount": 420_000, "salary_period": "monthly"}),
]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    )


def make_english_records(scenarios: list[dict]) -> list[dict]:
    records = []
    for scenario in scenarios:
        for variant in (1, 2, 3):
            records.append(
                {
                    "id": f"{scenario['scenario_id']}-v{variant}",
                    "scenario_id": scenario["scenario_id"],
                    "category": "calculation",
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
            )
    return records


def pidgin_question(scenario: dict) -> str:
    presentation = scenario["presentation"]
    amount = money(presentation["salary_amount"])
    facts = []
    for relief_id, value in scenario["relief_inputs"].items():
        if relief_id == "rent":
            facts.append(f"I dey pay {money(value)} for rent")
        elif relief_id == "pension":
            facts.append(f"I dey contribute {money(value)} to pension")
        else:
            facts.append(f"my {relief_id} contribution na {money(value)}")
    relief_text = "no deductions or reliefs" if not facts else ", and ".join(facts)
    if presentation["salary_period"] == "monthly":
        return f"I dey earn {amount} every month and {relief_text}. How much tax I go pay?"
    return f"I dey earn {amount} a year and {relief_text}. How much tax I go pay?"


def pidgin_answer(scenario: dict) -> str:
    truth = scenario["ground_truth"]
    presentation = scenario["presentation"]
    lines = [
        "I dey treat this as a Nigeria 2026 calculation from the facts wey you give. This na estimate under the Nigeria Tax Act 2025."
    ]
    if presentation["salary_period"] == "monthly":
        lines.append(
            f"Monthly income na {money(presentation['salary_amount'])} x 12 = {money(truth['gross_annual_salary'])} gross annual income."
        )
    else:
        lines.append(f"Gross annual income na {money(truth['gross_annual_salary'])}.")
    if truth["applied_reliefs"]:
        deductions = "; ".join(
            f"{key} deduction na {money(value)}"
            for key, value in truth["applied_reliefs"].items()
        )
        lines.append(f"Deductions wey apply na {deductions}.")
    else:
        lines.append("No deductions apply from the facts wey you give.")
    lines.append(f"Chargeable income na {money(truth['expected_chargeable_income'])}.")
    bands = "; ".join(
        f"{money(item['taxed_amount'])} at {percentage(item['rate'])} = {money(item['tax'])}"
        for item in truth["tax_breakdown"]
        if Decimal(str(item["tax"])) > 0
    )
    if bands:
        lines.append(f"Band calculation na {bands}.")
    lines.append(f"Estimated annual tax na {money(truth['expected_total_tax'])}.")
    lines.append(
        "Claims fit require documentary evidence under section 32. Relevant sources na sections 30(1), 30(2)(a), 32, and the Fourth Schedule."
    )
    return " ".join(lines)


def make_pidgin_calculations(scenarios: list[dict]) -> list[dict]:
    selected = [scenarios[index] for index in (0, 2, 10, 14)]
    records = []
    for scenario in selected:
        records.append(
            {
                "id": f"{scenario['scenario_id']}-pidgin",
                "scenario_id": scenario["scenario_id"],
                "category": "calculation",
                "language": "pcm",
                "instruction": pidgin_question(scenario),
                "output": pidgin_answer(scenario),
                "ground_truth": copy.deepcopy(scenario["ground_truth"]),
                "verified_by_engine": True,
                "verification": "engine",
                "source_fact_ids": scenario["source_fact_ids"],
                "scenario_family": scenario["scenario_family"],
                "generated_by": "deterministic_template",
                "human_reviewed": False,
                "source_verified": True,
            }
        )
    return records


def make_pidgin_behavior() -> list[dict]:
    common = {
        "language": "pcm",
        "verified_by_engine": False,
        "verification": "source_register",
        "generated_by": "manual",
        "human_reviewed": False,
        "source_verified": True,
    }
    rows = [
        {
            "id": "target-v6-pcm-bands",
            "category": "statutory_fact",
            "instruction": "Which individual income-tax bands dey for Nigeria for 2026?",
            "output": "The bands be: first NGN 800,000 at 0%; next NGN 2,200,000 at 15%; next NGN 9,000,000 at 18%; next NGN 13,000,000 at 21%; next NGN 25,000,000 at 23%; and anything above NGN 50,000,000 at 25%, under the Fourth Schedule to the Nigeria Tax Act 2025.",
            "source_fact_ids": ["F-001"],
            "scenario_family": "target_v6_pcm_statutory",
        },
        {
            "id": "target-v6-pcm-rent",
            "category": "statutory_fact",
            "instruction": "How dem dey calculate rent relief for Nigeria 2026 tax?",
            "output": "Rent relief na 20% of the annual rent wey you pay, but e no fit pass NGN 500,000. You must declare the real rent correctly, and section 32 fit require evidence.",
            "source_fact_ids": ["F-004", "F-005"],
            "scenario_family": "target_v6_pcm_statutory",
        },
        {
            "id": "target-v6-pcm-proof",
            "category": "statutory_fact",
            "instruction": "Wetin fit happen if I no get proof for deduction?",
            "output": "Under section 32, the tax authority fit ask for documentary evidence and fit refuse or reduce the deduction if the proof no dey or e no good enough.",
            "source_fact_ids": ["F-005"],
            "scenario_family": "target_v6_pcm_statutory",
        },
        {
            "id": "target-v6-pcm-default",
            "category": "scope_behavior",
            "instruction": "I no mention country or tax year. Wetin you go assume?",
            "output": "I go assume say na Nigeria and the 2026 year of assessment. If you mean another country or year, tell me; this version na for Nigerian personal-income-tax questions for 2026.",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "target_v6_pcm_scope",
        },
        {
            "id": "target-v6-pcm-country",
            "category": "scope_behavior",
            "instruction": "Calculate my Ghana personal income tax for 2026.",
            "output": "I no fit calculate Ghanaian tax. This version na for Nigerian personal income tax for the 2026 year of assessment.",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "target_v6_pcm_scope",
        },
        {
            "id": "target-v6-pcm-year",
            "category": "scope_behavior",
            "instruction": "Calculate my Nigerian tax under the 2025 rules.",
            "output": "I no fit reliably calculate the 2025 rules for this version. My scope na Nigerian personal income tax for the 2026 year of assessment.",
            "source_fact_ids": ["F-001", "F-002"],
            "scenario_family": "target_v6_pcm_scope",
        },
        {
            "id": "target-v6-pcm-period",
            "category": "clarification",
            "instruction": "I dey earn NGN 300,000. Calculate my tax.",
            "output": "NGN 300,000 na monthly or annual income? I need the period before I calculate.",
            "source_fact_ids": ["F-002", "F-003", "F-005"],
            "scenario_family": "target_v6_pcm_clarification",
        },
    ]
    return [{**common, **row, "ground_truth": None} for row in rows]


def main() -> None:
    ruleset = load_ruleset()
    scenarios = []
    for index, target in enumerate(TARGETS):
        _, reliefs, presentation = target
        if reliefs:
            family = "target_v6_reliefs"
        elif presentation["salary_period"] == "monthly":
            family = "target_v6_monthly"
        else:
            family = "target_v6_boundaries"
        scenarios.append(
            build_scenario(
                index,
                "target-v6",
                family,
                None,
                ruleset,
                forced_inputs=target,
            )
        )
    write_jsonl(ROOT / "data/scenarios/targeted_v6.jsonl", scenarios)
    write_jsonl(ROOT / "data/train/targeted_v6_english.jsonl", make_english_records(scenarios))
    write_jsonl(
        ROOT / "data/train/targeted_v6_pidgin_draft.jsonl",
        make_pidgin_calculations(scenarios) + make_pidgin_behavior(),
    )
    print(f"scenarios: {len(scenarios)}")
    print(f"English records: {len(scenarios) * 3}")
    print("Pidgin draft records: 11")


if __name__ == "__main__":
    main()
