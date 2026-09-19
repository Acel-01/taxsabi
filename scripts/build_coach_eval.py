#!/usr/bin/env python3
"""Build the coach-behavior eval — 15 prompts for the product vision.

Covers relief discovery, savings modeling, sequencing, filing workflow
(timing/channel/refunds), evidence guidance, VPC setup, employer duties,
scope handling, and multi-relief math. Computable prompts carry engine ground
truth; every prompt carries a checklist for the LLM judge (constitution §5-7).

Run after any training-data change to re-verify zero overlap:
    uv run python scripts/build_coach_eval.py --verify-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset, run_counterfactual  # noqa: E402

# Each entry: id, category, language, prompt, scenario, checklist.
# scenario: ("calc", gross, reliefs) | ("counterfactual", gross, base, field, value) | None
PROMPTS: list[dict] = [
    {
        "id": "coach-01",
        "category": "relief_discovery",
        "language": "en",
        "prompt": "I'm a salaried employee on NGN 6,000,000 a year. I rent my flat and I've never claimed anything. What am I missing?",
        "scenario": None,
        "checklist": [
            "Mentions rent relief (20% of annual rent, capped at NGN 500,000) and asks for the rent figure rather than asserting it",
            "Mentions pension contributions as adjustable levers, and asks about mortgage interest, NHF, NHIS, life insurance rather than asserting they apply (5.1)",
            "Ties the advice to documentation (one clause, not a paragraph) (5.5)",
            "Does not invent relief categories that do not exist (no CRA, no school fees)",
        ],
    },
    {
        "id": "coach-02",
        "category": "savings_modeling",
        "language": "en",
        "prompt": "My salary is NGN 9,600,000 a year. I'm considering putting NGN 480,000 into voluntary pension this year. How much tax would that save me?",
        "scenario": ("counterfactual", 9_600_000, {}, "pension", 480_000),
        "checklist": [
            "States the saving as NGN 86,400 (18% of the contribution at this income)",
            "Explains the marginal-rate logic briefly (every naira of relief saves the band rate)",
            "Notes the saving is achieved through the annual return/reconciliation, not month-by-month",
        ],
    },
    {
        "id": "coach-03",
        "category": "savings_modeling",
        "language": "en",
        "prompt": "I earn NGN 7,200,000 a year and pay NGN 3,000,000 rent. If I claim the rent relief, how much tax does it save me?",
        "scenario": ("counterfactual", 7_200_000, {}, "rent", 3_000_000),
        "checklist": [
            "Applies the cap correctly: relief is NGN 500,000 (20% of 3m is 600k, capped at 500k)",
            "States the saving as NGN 90,000 (18% of the capped relief)",
            "Explains why the cap binds",
        ],
    },
    {
        "id": "coach-04",
        "category": "marginal_rate",
        "language": "en",
        "prompt": "I earn NGN 13,000,000 a year. A friend said every NGN 100,000 of relief is worth NGN 25,000 to me. Is that right?",
        "scenario": ("counterfactual", 13_000_000, {}, "pension", 100_000),
        "checklist": [
            "Corrects the friend: at 13m the marginal rate is 21%, so the saving is NGN 21,000 per NGN 100,000",
            "Explains the bands and the marginal rate reached without dumping the whole table",
            "Does not simply agree with the wrong claim",
        ],
    },
    {
        "id": "coach-05",
        "category": "sequencing",
        "language": "en",
        "prompt": "I have about NGN 600,000 of spare savings this year, earning NGN 13,000,000. Should I put it into voluntary pension or something else?",
        "scenario": None,
        "checklist": [
            "Leads with the flexible lever (voluntary pension) and its rules (one-third cap, once monthly, through employer)",
            "Mentions the 5-year rule on withdrawal of earned income and the 50/50 contingent/fixed split",
            "Frames the choice as legal optimization, not avoidance (5.4), and mentions documentation",
            "Does not assert other reliefs apply without asking",
        ],
    },
    {
        "id": "coach-06",
        "category": "filing_timing",
        "language": "en",
        "prompt": "My employer deducts PAYE monthly. I just paid two years of rent and I will file the relief claim next month. Will the relief apply from the month it is approved, or is it backdated?",
        "scenario": None,
        "checklist": [
            "Explains the annual-liability model: PAYE is instalments; the relief attaches to the year of assessment",
            "States that over-deducted tax is recovered by refund or set-off/credit, not by a month-by-month switch (F-018)",
            "Mentions the refund route: audit, 90-day payment window, written claim within six years",
            "Does not promise a specific approval timeline",
        ],
    },
    {
        "id": "coach-07",
        "category": "filing_channel",
        "language": "en",
        "prompt": "Where do I actually submit a rent relief claim, and what do I upload with it?",
        "scenario": None,
        "checklist": [
            "Names the annual return channel: relevant state tax authority; LIRS e-Tax platform for Lagos (F-017)",
            "Names Tax Form A as the return of income and claims for reliefs",
            "Lists the evidence for reliefs: pension, life assurance, NHIS, NHF records; rent documentation",
            "Notes every employee files the annual return even when PAYE already covers the tax",
        ],
    },
    {
        "id": "coach-08",
        "category": "refund_process",
        "language": "en",
        "prompt": "If the PAYE my employer deducted this year turns out to be more than my final tax after reliefs, what happens to the difference?",
        "scenario": None,
        "checklist": [
            "Explains refund or set-off/credit against future liabilities (F-018)",
            "Mentions the audit, the 90-day window after the decision, and the six-year written claim limit",
            "Warns that false claims are penalised (recovery plus 50% plus interest)",
        ],
    },
    {
        "id": "coach-09",
        "category": "evidence_guidance",
        "language": "en",
        "prompt": "What documents do I need to keep for a rent relief claim?",
        "scenario": None,
        "checklist": [
            "Mentions the claim must be in writing in the prescribed form and evidence may be demanded (F-005)",
            "Mentions accurate declaration of the actual rent paid (F-004)",
            "References the filing-practice evidence list where relevant (pension, life assurance, NHIS, NHF mandatory for those reliefs) (F-012)",
            "Does not invent a specific form number that is not in the register",
        ],
    },
    {
        "id": "coach-10",
        "category": "vpc_setup",
        "language": "en",
        "prompt": "How do I start a voluntary pension contribution, step by step?",
        "scenario": None,
        "checklist": [
            "Steps: confirm eligibility/active RSA, decide amount, notify employer in writing, employer remits to the PFC, keep RSA statements",
            "Limits: not more than one-third of monthly salary, once a month, Naira only, through the employer (S8)",
            "Structure: 50% contingent / 50% fixed, two-year retention, withdrawal once every two years",
            "Tax: deductible when contributed; income taxed if withdrawn within five years (s.10(4))",
        ],
    },
    {
        "id": "coach-11",
        "category": "employer_duties",
        "language": "en",
        "prompt": "I just discovered my employer has been keeping pension deductions for weeks before remitting. What are the rules and penalties?",
        "scenario": None,
        "checklist": [
            "States the deadline: remit within seven working days from the day the employee is paid (F-016)",
            "States the penalty floor: not less than 2% of the unpaid contribution per month or part of a month, recoverable as a debt to the RSA",
            "Separates the PAYE clock (10th of following month) from the pension clock",
            "Suggests documenting the deductions and, where appropriate, raising it formally",
        ],
    },
    {
        "id": "coach-12",
        "category": "multi_relief_math",
        "language": "en",
        "prompt": "Work out my tax: salary NGN 8,400,000 a year, pension contributions NGN 500,000, rent NGN 2,400,000 a year, NHIS NGN 72,000 and NHF NGN 60,000.",
        "scenario": ("calc", 8_400_000, {"pension": 500_000, "rent": 2_400_000, "nhis": 72_000, "nhf": 60_000}),
        "checklist": [
            "Applies the rent relief at the capped NGN 480,000 (20% of 2.4m)",
            "Uses all four reliefs to reach chargeable income NGN 7,288,000",
            "States total tax NGN 1,101,840 with a clean band breakdown",
            "No invented reliefs or amounts",
        ],
    },
    {
        "id": "coach-13",
        "category": "minimum_wage",
        "language": "en",
        "prompt": "I earn the national minimum wage. My friend says I should still file tax and claim reliefs even though I pay no tax. Is that right?",
        "scenario": None,
        "checklist": [
            "Confirms minimum-wage earners (NGN 70,000/month) are exempt from income tax on chargeable income (F-009/F-015)",
            "Confirms the annual filing obligation still applies to taxable persons; filing has value for records/TCC and is an individual duty (F-017)",
            "Does not invent a filing exemption for minimum-wage earners",
        ],
    },
    {
        "id": "coach-14",
        "category": "scope",
        "language": "en",
        "prompt": "Can you help me compute the VAT my company must remit this month?",
        "scenario": None,
        "checklist": [
            "Declines clearly and briefly: VAT/company obligations are outside personal income tax scope (constitution 4.x)",
            "Does not attempt the computation or invent VAT rules",
            "Offers what it can help with (personal income tax for employees)",
        ],
    },
    {
        "id": "coach-15",
        "category": "raise_planning",
        "language": "en",
        "prompt": "I'm getting a raise next month that takes me from NGN 9,600,000 to NGN 12,000,000 a year. How should I plan so the extra tax doesn't eat the whole increase?",
        "scenario": None,
        "checklist": [
            "Models the raise: shows the marginal rate change and the tax on the increment",
            "Proactively suggests adjusting voluntary pension contributions to offset the increase (5.6)",
            "Respects the one-third cap and the other VPC rules",
            "Keeps the tone as legal optimization (5.4)",
        ],
    },
]


def money(value) -> str:
    return format(value, ".2f")


def scenario_truth(scenario, ruleset: dict) -> dict | None:
    if scenario is None:
        return None
    kind = scenario[0]
    if kind == "calc":
        _, gross, reliefs = scenario
        result = calculate_full(gross, reliefs, ruleset)
        return {
            "kind": "calc",
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in reliefs.items()},
            },
            "ground_truth": {
                "expected_chargeable_income": money(result["chargeable_income"]),
                "expected_total_tax": money(result["total_tax"]),
            },
        }
    if kind == "counterfactual":
        _, gross, base_reliefs, field, value = scenario
        result = run_counterfactual(gross, base_reliefs, field, value, ruleset)
        return {
            "kind": "counterfactual",
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in base_reliefs.items()},
                "changed_field": field,
                "new_value": money(value),
            },
            "ground_truth": {
                "expected_chargeable_income": money(result["scenario_chargeable_income"]),
                "expected_total_tax": money(result["scenario_tax"]),
                "expected_savings": money(result["delta"]),
            },
        }
    raise ValueError(f"unknown scenario kind: {kind}")


def build_records() -> list[dict]:
    ruleset = load_ruleset()
    records = []
    for prompt in PROMPTS:
        record = {
            "id": prompt["id"],
            "language": prompt["language"],
            "category": prompt["category"],
            "prompt": prompt["prompt"],
            "checklist": prompt["checklist"],
        }
        truth = scenario_truth(prompt["scenario"], ruleset)
        if truth is not None:
            record.update(truth)
        records.append(record)
    return records


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def verify(records: list[dict]) -> list[str]:
    problems = []
    train_dir = ROOT / "data" / "train"
    train_prompts = set()
    for path in train_dir.glob("*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in ("instruction", "prompt"):
                if row.get(key):
                    train_prompts.add(normalize(row[key]))
    for record in records:
        if normalize(record["prompt"]) in train_prompts:
            problems.append(f"overlap with training: {record['id']}")
        if not record.get("checklist"):
            problems.append(f"missing checklist: {record['id']}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "eval" / "coach_eval.jsonl")
    args = parser.parse_args()

    records = build_records()
    problems = verify(records)
    if problems:
        print(f"FAIL: {len(problems)} problems")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)

    if not args.verify_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"wrote {len(records)} coach prompts -> {args.out}")

    scored = [r for r in records if r.get("ground_truth")]
    print("verified: zero training overlap, all prompts carry judge checklists")
    print(f"  engine-scorable records: {len(scored)}")


if __name__ == "__main__":
    main()
