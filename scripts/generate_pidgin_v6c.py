#!/usr/bin/env python3
"""Generate Pidgin v6c records targeting observed Pidgin robustness gaps."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_scenarios import build_scenario
from generate_targeted_v6 import pidgin_question
from render_seed_dataset import money, percentage, shorthand_money
from rules_engine.engine import load_ruleset


TARGETS = [
    (799_999, {}, {"salary_amount": 799_999, "salary_period": "annual"}),
    (800_000, {}, {"salary_amount": 800_000, "salary_period": "annual"}),
    (800_001, {}, {"salary_amount": 800_001, "salary_period": "annual"}),
    (3_000_000, {}, {"salary_amount": 3_000_000, "salary_period": "annual"}),
    (4_800_000, {"rent": 2_500_000}, {"salary_amount": 4_800_000, "salary_period": "annual"}),
    (3_000_000, {}, {"salary_amount": 250_000, "salary_period": "monthly"}),
    (6_000_000, {}, {"salary_amount": 500_000, "salary_period": "monthly"}),
    (2_000_000, {"rent": 2_500_000, "pension": 300_000}, {"salary_amount": 2_000_000, "salary_period": "annual"}),
]


def concise_pidgin_answer(scenario: dict) -> str:
    truth = scenario["ground_truth"]
    presentation = scenario["presentation"]
    lines = []
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
    )
    if bands:
        lines.append(f"Band calculation na {bands}.")
    lines.append(f"Estimated annual tax na {money(truth['expected_total_tax'])}.")
    lines.append(
        "Claims fit require documentary evidence under section 32. Relevant sources na sections 30(1), 30(2)(a), 32, and the Fourth Schedule."
    )
    return " ".join(lines)


def variant_abeg(scenario: dict) -> str:
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
    relief_text = "i no dey get any deductions or reliefs" if not facts else ", and ".join(facts)
    if presentation["salary_period"] == "monthly":
        return f"I dey earn {amount} every month and {relief_text}. How much tax I go pay? Abeg show the calculation."
    return f"I dey earn {amount} a year and {relief_text}. How much tax I go pay? Abeg show the calculation."


def variant_shorthand(scenario: dict) -> str:
    presentation = scenario["presentation"]
    amount = shorthand_money(presentation["salary_amount"])
    facts = []
    for relief_id, value in scenario["relief_inputs"].items():
        if relief_id == "rent":
            facts.append(f"I dey pay {shorthand_money(value)} for rent")
        elif relief_id == "pension":
            facts.append(f"I dey contribute {shorthand_money(value)} to pension")
        else:
            facts.append(f"my {relief_id} contribution na {shorthand_money(value)}")
    relief_text = "i no dey get any deductions or reliefs" if not facts else ", and ".join(facts)
    if presentation["salary_period"] == "monthly":
        return f"I dey earn {amount} every month and {relief_text}. How much tax I go pay?"
    return f"I dey earn {amount} a year and {relief_text}. How much tax I go pay?"


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))


def main() -> None:
    ruleset = load_ruleset()
    scenarios = []
    records = []
    for index, target in enumerate(TARGETS):
        _, reliefs, presentation = target
        family = "target_v6c_pcm_reliefs" if reliefs else "target_v6c_pcm_monthly" if presentation["salary_period"] == "monthly" else "target_v6c_pcm_boundaries"
        scenario = build_scenario(
            index,
            "target-v6c",
            family,
            None,
            ruleset,
            forced_inputs=target,
        )
        scenarios.append(scenario)
        for variant, question in (
            (1, pidgin_question(scenario)),
            (2, variant_abeg(scenario)),
            (3, variant_shorthand(scenario)),
        ):
            records.append(
                {
                    "id": f"{scenario['scenario_id']}-pidgin-v{variant}",
                    "scenario_id": scenario["scenario_id"],
                    "category": "calculation",
                    "language": "pcm",
                    "instruction": question,
                    "output": concise_pidgin_answer(scenario),
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
    write_jsonl(ROOT / "data/scenarios/targeted_v6c.jsonl", scenarios)
    write_jsonl(ROOT / "data/train/targeted_v6c_pidgin_draft.jsonl", records)
    print(f"wrote {len(scenarios)} scenarios")
    print(f"wrote {len(records)} Pidgin draft records")


if __name__ == "__main__":
    main()
