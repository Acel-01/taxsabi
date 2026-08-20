#!/usr/bin/env python3
"""Generate a content-clean held-out evaluation set for v6 model selection."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_counterfactual_dataset import build_pair
from generate_scenarios import build_scenario
from render_seed_dataset import answer_text, money, question_variants
from rules_engine.engine import load_ruleset


CALC_TARGETS = [
    (799_997, {}, {"salary_amount": 799_997, "salary_period": "annual"}),
    (800_003, {}, {"salary_amount": 800_003, "salary_period": "annual"}),
    (2_999_998, {}, {"salary_amount": 2_999_998, "salary_period": "annual"}),
    (3_000_002, {}, {"salary_amount": 3_000_002, "salary_period": "annual"}),
    (11_999_998, {}, {"salary_amount": 11_999_998, "salary_period": "annual"}),
    (12_000_002, {}, {"salary_amount": 12_000_002, "salary_period": "annual"}),
    (24_999_998, {}, {"salary_amount": 24_999_998, "salary_period": "annual"}),
    (25_000_002, {}, {"salary_amount": 25_000_002, "salary_period": "annual"}),
    (49_999_998, {}, {"salary_amount": 49_999_998, "salary_period": "annual"}),
    (50_000_003, {}, {"salary_amount": 50_000_003, "salary_period": "annual"}),
    (3_300_000, {}, {"salary_amount": 275_000, "salary_period": "monthly"}),
    (5_200_000, {"rent": 2_400_000, "pension": 180_000}, {"salary_amount": 5_200_000, "salary_period": "annual"}),
]

COUNTERFACTUAL_TARGETS = [
    (1_400_000, {}, {"salary_amount": 1_400_000, "salary_period": "annual"}),
    (2_600_000, {"rent": 600_000}, {"salary_amount": 2_600_000, "salary_period": "annual"}),
    (3_800_000, {"rent": 1_200_000}, {"salary_amount": 3_800_000, "salary_period": "annual"}),
    (7_800_000, {}, {"salary_amount": 7_800_000, "salary_period": "annual"}),
    (12_400_000, {"nhf": 60_000}, {"salary_amount": 12_400_000, "salary_period": "annual"}),
    (26_000_000, {}, {"salary_amount": 26_000_000, "salary_period": "annual"}),
    (51_000_000, {"pension": 600_000}, {"salary_amount": 51_000_000, "salary_period": "annual"}),
    (4_200_000, {}, {"salary_amount": 350_000, "salary_period": "monthly"}),
]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))


def clean_calculation_record(scenario: dict) -> dict:
    truth = scenario["ground_truth"]
    presentation = scenario["presentation"]
    if presentation["salary_period"] == "monthly":
        income = f"{money(presentation['salary_amount'])} per month"
    else:
        income = f"{money(truth['gross_annual_salary'])} gross annual income"
    reliefs = []
    for key, value in truth["relief_inputs"].items():
        reliefs.append(f"{key} payments of {money(value)}")
    relief_text = "no relief claims" if not reliefs else ", ".join(reliefs)
    instruction = (
        "For a Nigerian personal-income-tax estimate under the 2026 rules, "
        f"use {income} and {relief_text}. Give the chargeable income, band breakdown, "
        "and final annual tax."
    )
    return {
        "id": f"{scenario['scenario_id']}-v1",
        "scenario_id": scenario["scenario_id"],
        "category": "calculation",
        "language": "en",
        "instruction": instruction,
        "output": answer_text(scenario, 1),
        "ground_truth": copy.deepcopy(truth),
        "verified_by_engine": True,
        "verification": "engine",
        "source_fact_ids": scenario["source_fact_ids"],
        "scenario_family": scenario["scenario_family"],
        "generated_by": "deterministic_template",
        "human_reviewed": False,
    }


def behavior_records() -> list[dict]:
    common = {
        "language": "en",
        "verified_by_engine": False,
        "verification": "source_register",
        "generated_by": "manual",
        "human_reviewed": True,
        "source_verified": True,
        "ground_truth": None,
    }
    rows = [
        ("clean-v6-fact-bands", "statutory_fact", "State the six individual chargeable-income bands and rates for the 2026 assessment.", "Under the Fourth Schedule to the Nigeria Tax Act 2025, the bands are: first NGN 800,000 at 0%; next NGN 2,200,000 at 15%; next NGN 9,000,000 at 18%; next NGN 13,000,000 at 21%; next NGN 25,000,000 at 23%; and amounts above NGN 50,000,000 at 25%.", ["F-001"], "clean_v6_fact"),
        ("clean-v6-fact-rent", "statutory_fact", "What is the statutory limit on rent relief for a Nigerian individual in 2026?", "Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required under section 32.", ["F-004", "F-005"], "clean_v6_fact"),
        ("clean-v6-fact-nhf", "statutory_fact", "What is the private-sector treatment of NHF contributions?", "For private-sector employees, NHF contribution is voluntary under the NHF Act 1992 as amended by section 45 of the Business Facilitation (Miscellaneous Provisions) Act 2022. NHF contributions are separately listed as an eligible deduction under section 30(2)(a)(i) of the Nigeria Tax Act 2025.", ["F-006", "F-003"], "clean_v6_fact"),
        ("clean-v6-fact-proof", "statutory_fact", "Can a tax authority reduce a deduction when the supporting evidence is inadequate?", "Yes. Under section 32, the relevant tax authority may require documentary evidence and may refuse or reduce a deduction claim if the evidence is absent or inadequate.", ["F-005"], "clean_v6_fact"),
        ("clean-v6-scope-default", "scope_behavior", "Which jurisdiction and assessment year does this assistant use when the user gives neither?", "I default to Nigeria and the 2026 year of assessment, and I will state that assumption.", ["F-001", "F-002"], "clean_v6_scope"),
        ("clean-v6-scope-country", "scope_behavior", "Please calculate my personal income tax under Kenya's 2026 rules.", "I cannot calculate Kenyan tax. This version supports Nigerian personal income tax for the 2026 year of assessment.", ["F-001", "F-002"], "clean_v6_scope"),
        ("clean-v6-scope-year", "scope_behavior", "Please apply the Nigerian 2027 tax rules to my income.", "I cannot reliably calculate the 2027 rules. This version supports Nigerian personal income tax for 2026.", ["F-001", "F-002"], "clean_v6_scope"),
        ("clean-v6-clarify-period", "clarification", "My income is NGN 420,000 and I want the tax estimate. What else do you need?", "Is NGN 420,000 monthly or annual income? I need the period before I calculate tax.", ["F-002", "F-003", "F-005"], "clean_v6_clarification"),
    ]
    return [
        {
            **common,
            "id": record_id,
            "category": category,
            "instruction": instruction,
            "output": output,
            "source_fact_ids": source_ids,
            "scenario_family": family,
        }
        for record_id, category, instruction, output, source_ids, family in rows
    ]


def main() -> None:
    ruleset = load_ruleset()
    scenarios = []
    records = []
    for index, target in enumerate(CALC_TARGETS):
        scenario = build_scenario(
            index,
            "clean-v6-calc",
            "clean_v6_boundaries" if index < 10 else "clean_v6_monthly" if index == 10 else "clean_v6_reliefs",
            None,
            ruleset,
            forced_inputs=target,
        )
        scenarios.append(scenario)
        records.append(clean_calculation_record(scenario))

    for index, target in enumerate(COUNTERFACTUAL_TARGETS):
        base = build_scenario(
            index,
            "clean-v6-base",
            "clean_v6_counterfactual_base",
            None,
            ruleset,
            forced_inputs=target,
        )
        scenario, record = build_pair(index, "clean-v6", base, ruleset)
        scenarios.append(scenario)
        records.append(record)

    records.extend(behavior_records())
    write_jsonl(ROOT / "data/scenarios/clean_eval_v6.jsonl", scenarios)
    write_jsonl(ROOT / "data/eval/final_eval_v6_clean.jsonl", records)
    print(f"wrote {len(scenarios)} scenario records")
    print(f"wrote {len(records)} clean evaluation records")


if __name__ == "__main__":
    main()
