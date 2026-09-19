#!/usr/bin/env python3
"""Build the paraphrase-consistency suite — 20 core questions x 5 phrasings.

Every core is asked five different ways; the model's answers must agree across
phrasings (same facts, same amounts). Calculation cores carry engine-computed
ground truth, identical across the five variants.

Run after any training-data change to re-verify zero overlap:
    uv run python scripts/build_paraphrase_suite.py --verify-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset, run_counterfactual  # noqa: E402

# Each core: id, category, kind ("calc" | "counterfactual" | "fact"),
# scenario, and five phrasings. Variant labels: a=standard, b=casual,
# c=terse/shorthand, d=verbose/context, e=indirect/second-hand.
CORES: list[dict] = [
    {
        "id": "para-calc-01",
        "category": "calculation",
        "kind": "calc",
        "scenario": (1_450_000, {}),
        "variants": [
            "I earn NGN 1,450,000 a year and no deductions or reliefs. How much tax do I pay?",
            "So my yearly pay is 1.45m and I have no reliefs. What do I pay?",
            "1.45m/yr, zero reliefs - tax?",
            "I'm trying to plan my budget for next year. My gross annual salary will be NGN 1,450,000, I don't contribute to any scheme and I don't claim any reliefs. What would my income tax be?",
            "A colleague told me someone on a 1.45m annual salary with no reliefs pays nothing. Is that right, and what is the actual tax?",
        ],
    },
    {
        "id": "para-calc-02",
        "category": "calculation",
        "kind": "calc",
        "scenario": (1_080_000, {}),
        "variants": [
            "I earn NGN 90,000 every month with no deductions. What is my annual tax?",
            "90k enters my account every month, no deductions. How much tax for the whole year?",
            "90k/month. Annual tax?",
            "I get paid NGN 90,000 at the end of every month and I have no deductions at all. Please work out my total tax for the year.",
            "Someone said a person earning 90,000 a month pays about 42,000 tax a year. Is that calculation correct?",
        ],
    },
    {
        "id": "para-calc-03",
        "category": "calculation",
        "kind": "calc",
        "scenario": (5_750_000, {"rent": 1_800_000}),
        "variants": [
            "I earn NGN 5,750,000 a year and pay NGN 1,800,000 in rent. How much tax do I pay?",
            "My salary is 5.75m for the year and my rent is 1.8m. What is my tax?",
            "5.75m/yr, rent 1.8m. Tax?",
            "I'm gathering figures for my annual return. Gross salary of NGN 5,750,000 and annual rent of NGN 1,800,000. Can you compute my income tax after the rent relief?",
            "My friend with a 5.75m salary and 1.8m rent says his tax comes to about 900k. Is that figure right?",
        ],
    },
    {
        "id": "para-calc-04",
        "category": "calculation",
        "kind": "calc",
        "scenario": (8_400_000, {"pension": 500_000, "nhis": 72_000}),
        "variants": [
            "I earn NGN 8,400,000 a year, contribute NGN 500,000 to pension and NGN 72,000 to NHIS. How much tax do I pay?",
            "I earn 8.4m yearly. I contribute 500k to pension and 72k to NHIS. What will I pay?",
            "8.4m/yr + pension 500k + NHIS 72k. Tax?",
            "Before I file, I want to be sure of the numbers: annual salary NGN 8,400,000, annual pension contributions NGN 500,000, NHIS contributions NGN 72,000. What is my chargeable income and tax?",
            "I was told that with an 8.4m salary, 500k pension and 72k NHIS, my tax should be around 1.4m. Can you verify?",
        ],
    },
    {
        "id": "para-calc-05",
        "category": "calculation",
        "kind": "calc",
        "scenario": (2_700_000, {"rent": 450_000}),
        "variants": [
            "I earn NGN 2,700,000 a year and pay NGN 450,000 rent. How much tax do I pay?",
            "My pay is 2.7m for the year and rent is 450k. How much tax?",
            "2.7m/yr, rent 450k. Tax?",
            "I am putting my tax records together: gross annual income NGN 2,700,000 and I paid NGN 450,000 as rent for the year. Please calculate my tax liability.",
            "My brother says a 2.7m salary with 450k rent attracts tax of roughly 271,500. Is he correct?",
        ],
    },
    {
        "id": "para-calc-06",
        "category": "counterfactual",
        "kind": "counterfactual",
        "scenario": (13_000_000, {}, "pension", 300_000),
        "variants": [
            "I earn NGN 13,000,000 a year and make no contributions. If I contribute NGN 300,000 to voluntary pension this year, what will my tax be and how much will it save me?",
            "13m salary, nothing is deducted. If I add 300k voluntary pension, what will my tax be and how much will I save?",
            "13m/yr, add 300k VPC - new tax and savings?",
            "I'm considering voluntary pension contributions as a year-end move. Annual income is NGN 13,000,000 with no other contributions; if I put NGN 300,000 into voluntary pension, what is my tax afterwards and the saving versus doing nothing?",
            "An adviser told me a 300k voluntary pension on a 13m salary saves about 63k tax. Can you check that claim?",
        ],
    },
    {
        "id": "para-calc-07",
        "category": "counterfactual",
        "kind": "counterfactual",
        "scenario": (5_000_000, {}, "rent", 2_400_000),
        "variants": [
            "I earn NGN 5,000,000 a year. I'm about to sign a NGN 2,400,000 annual rent. How much tax will I pay after the rent relief, and how much does the relief save me?",
            "My salary is 5m and I want to rent a place that costs 2.4m a year. After rent relief, what is my tax and how much does the relief save me?",
            "5m/yr, rent 2.4m - tax and savings from relief?",
            "I am comparing locations: annual income NGN 5,000,000, and one option means paying NGN 2,400,000 in rent for the year. With the rent relief applied, what would my tax be and what is the saving from the relief?",
            "Someone claims a 2.4m rent on a 5m salary cuts tax by about 86,400. Is that right, and what is the tax after the relief?",
        ],
    },
    {
        "id": "para-calc-08",
        "category": "calculation",
        "kind": "calc",
        "scenario": (32_000_000, {"rent": 900_000}),
        "variants": [
            "I earn NGN 32,000,000 a year and pay NGN 900,000 in rent. How much tax do I pay?",
            "32m salary for the year, rent 900k. What is my tax?",
            "32m/yr, rent 900k. Tax?",
            "For my annual planning: gross income NGN 32,000,000, annual rent NGN 900,000. Please compute the chargeable income and total tax.",
            "I'm told tax on a 32m salary with 900k rent is over 6m. Can you confirm the exact figure?",
        ],
    },
    {
        "id": "para-fact-01",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "What are the individual income-tax bands and rates in Nigeria for the 2026 year of assessment?",
            "Which tax bands apply to an individual in 2026, and what is the rate for each?",
            "2026 PIT bands + rates?",
            "I'm updating my payroll spreadsheet and need to confirm the personal income tax rates for 2026, from the first band to the highest. Can you list them all?",
            "Someone said the top personal income tax rate for 2026 is 30%. Is that correct, and what are the bands?",
        ],
    },
    {
        "id": "para-fact-02",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "How is rent relief calculated, and is there a cap?",
            "How does the rent relief work, and is there a maximum?",
            "Rent relief: formula and cap?",
            "I want to understand the rent relief fully before I claim it in my return: how is it computed and what is the maximum amount allowed?",
            "A friend says rent relief gives you 20% back of whatever rent you pay, with no limit. Is that true?",
        ],
    },
    {
        "id": "para-fact-03",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "Which deductions can reduce my chargeable income under the Nigeria Tax Act 2025?",
            "What things can reduce my income before tax is calculated?",
            "List eligible deductions?",
            "I'm reviewing what I can legitimately claim this year. Please list the deduction categories available to individuals under the current tax law.",
            "Someone mentioned school fees and house rent as tax deductions. Which deductions actually exist under the 2025 Act?",
        ],
    },
    {
        "id": "para-fact-04",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "I earn the national minimum wage of NGN 70,000 a month. Do I pay income tax?",
            "I receive 70k every month, which is the minimum wage. Will tax be collected from me?",
            "70k/month minimum wage - taxable?",
            "My monthly pay is exactly the national minimum wage (NGN 70,000). I want to know whether I am expected to pay income tax on it, and if so how much.",
            "A colleague insists everyone earning above 30,000 a month pays tax, even at the minimum wage. Who is right?",
        ],
    },
    {
        "id": "para-fact-05",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "When is PAYE deducted from salaries due to be remitted to the tax authority?",
            "After my employer deducts PAYE from salary, when should the money be remitted?",
            "PAYE remittance deadline?",
            "I run payroll for a small company and want to get the compliance calendar right. What is the deadline for remitting PAYE after salaries are paid?",
            "Our accountant says PAYE for January salaries can be remitted any time in February up to the 21st. Is that correct?",
        ],
    },
    {
        "id": "para-fact-06",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "What are the mandatory pension contribution rates for employers and employees?",
            "How much do employer and worker contribute for pension?",
            "Pension contribution rates?",
            "I'm setting up payroll for a new company. Under the Pension Reform Act, what are the minimum rates that the employer and the employee must contribute, and what does the employer need to maintain for staff?",
            "Someone said employee pension contribution is 7.5% and employer 7.5%. Is that still correct?",
        ],
    },
    {
        "id": "para-fact-07",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "What are the rules for making voluntary pension contributions?",
            "How does voluntary pension contribution work - what are the rules?",
            "VPC rules and limits?",
            "I want to start making voluntary pension contributions this year. Please explain the rules: how much I can contribute, how often, and how the money moves into my account.",
            "Someone says you can voluntarily contribute any amount, any number of times a month, directly to your PFA. Is that correct?",
        ],
    },
    {
        "id": "para-fact-08",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "How are voluntary pension contributions taxed if I withdraw them early?",
            "If I withdraw my voluntary pension early, will it be taxed?",
            "Early VPC withdrawal - tax?",
            "I'm weighing voluntary pension contributions but may need the money within a few years. What is the tax treatment if I withdraw a voluntary contribution earlier than the long-term window?",
            "A friend says money earned on voluntary pension contributions is never taxed at all, even if you withdraw after one year. Is that right?",
        ],
    },
    {
        "id": "para-fact-09",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "What do I need to do to claim a tax deduction, and can the authority ask for proof?",
            "What do I need to claim my relief, and can they ask me for proof?",
            "Claim requirements + evidence?",
            "Before I claim deductions in my return, I want to understand the formalities: how claims must be made and what happens if the tax authority questions them.",
            "Someone says deductions are granted automatically once you qualify, with no paperwork. Is that correct?",
        ],
    },
    {
        "id": "para-fact-10",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "If I overpay my tax, how do I get a refund?",
            "If I pay more tax than I should, how do I collect the excess back?",
            "Overpaid tax - refund process?",
            "Suppose PAYE deducted during the year ends up higher than my final liability after reliefs. What is the process and the timelines for recovering the excess?",
            "Someone says overpaid tax is never refunded, only credited forever. What does the law actually provide?",
        ],
    },
    {
        "id": "para-fact-11",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "Where and how do I file my annual income tax return and claim reliefs?",
            "Where do I file my tax return and put my relief claims?",
            "Filing channel for relief claims?",
            "I'm preparing to file this year. Which platform and form do I use for my annual return, and where do relief claims go?",
            "A friend says relief claims are filed separately in a special office, not in the annual return. Is that true?",
        ],
    },
    {
        "id": "para-fact-12",
        "category": "statutory_fact",
        "kind": "fact",
        "scenario": None,
        "variants": [
            "Can I still claim the consolidated relief allowance?",
            "Is the consolidated relief allowance still there?",
            "CRA still exists?",
            "Some older tax articles I found describe a consolidated relief allowance that reduces taxable income. Does that allowance still exist under the current law, and what replaced it?",
            "Someone says the CRA still applies alongside rent relief. Is that correct?",
        ],
    },
]


def money(value) -> str:
    return format(value, ".2f")


def ground_truth_for(core: dict, ruleset: dict) -> dict | None:
    kind = core["kind"]
    if kind == "calc":
        gross, reliefs = core["scenario"]
        result = calculate_full(gross, reliefs, ruleset)
        return {
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in reliefs.items()},
            },
            "ground_truth": {
                "kind": "calc",
                "expected_chargeable_income": money(result["chargeable_income"]),
                "expected_total_tax": money(result["total_tax"]),
            },
        }
    if kind == "counterfactual":
        gross, base_reliefs, field, new_value = core["scenario"]
        result = run_counterfactual(gross, base_reliefs, field, new_value, ruleset)
        return {
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in base_reliefs.items()},
                "changed_field": field,
                "new_value": money(new_value),
            },
            "ground_truth": {
                "kind": "counterfactual",
                "expected_chargeable_income": money(result["scenario_chargeable_income"]),
                "expected_total_tax": money(result["scenario_tax"]),
                "expected_savings": money(result["delta"]),
            },
        }
    return None


def build_records() -> list[dict]:
    ruleset = load_ruleset()
    records = []
    for core in CORES:
        truth = ground_truth_for(core, ruleset)
        for index, prompt in enumerate(core["variants"]):
            label = chr(ord("a") + index)
            record = {
                "id": f"{core['id']}-{label}",
                "consistency_group": core["id"],
                "variant": label,
                "language": "en",
                "category": core["category"],
                "prompt": prompt,
            }
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
    seen: dict[str, str] = {}
    for record in records:
        key = normalize(record["prompt"])
        if key in seen:
            problems.append(f"duplicate phrasing: {record['id']} == {seen[key]}")
        seen[key] = record["id"]
    groups: dict[str, list[str]] = {}
    for record in records:
        groups.setdefault(record["consistency_group"], []).append(record["variant"])
    for group, variants in groups.items():
        if sorted(variants) != ["a", "b", "c", "d", "e"]:
            problems.append(f"group {group} variants wrong: {variants}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "eval" / "paraphrase_suite.jsonl")
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
        print(f"wrote {len(records)} prompts ({len(CORES)} cores x 5) -> {args.out}")

    scored = [r for r in records if r.get("ground_truth")]
    print("verified: zero training overlap, no duplicate phrasings, complete groups")
    print(f"  engine-scorable records: {len(scored)}")


if __name__ == "__main__":
    main()
