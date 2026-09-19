#!/usr/bin/env python3
"""Build the multi-turn probe suite — 10 conversation scripts, 3-5 turns each.

Tests cross-turn behavior: fact retention, corrections, clarification,
language maintenance, topic switching, and long-context recall. Calculation
turns carry engine-computed ground truth for scoring.

Run after any training-data change to re-verify zero overlap:
    uv run python scripts/build_multiturn_suite.py --verify-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset, run_counterfactual  # noqa: E402

# Each conversation: id, title, language, turns.
# A turn: {"user": str, "calc": (gross, reliefs) | "counterfactual": (gross, base, field, value) | "note": str}
CONVERSATIONS: list[dict] = [
    {
        "id": "mt-01",
        "title": "calc progression with follow-up relief",
        "language": "en",
        "turns": [
            {"user": "I earn NGN 3,600,000 a year and have no deductions or reliefs. How much tax do I pay?", "calc": (3_600_000, {})},
            {"user": "I forgot - I also pay NGN 1,200,000 rent a year. Recompute with that.", "calc": (3_600_000, {"rent": 1_200_000})},
            {"user": "How much did the rent relief actually save me in naira?", "counterfactual": (3_600_000, {}, "rent", 1_200_000)},
        ],
    },
    {
        "id": "mt-02",
        "title": "user corrects a previously stated figure",
        "language": "en",
        "turns": [
            {"user": "My annual salary is NGN 4,200,000 with no reliefs. What is my tax?", "calc": (4_200_000, {})},
            {"user": "Sorry, I misread my contract. It's NGN 4,800,000 a year, not 4.2m. What is the tax now?", "calc": (4_800_000, {})},
            {"user": "And I pay 600k rent a year. So what's my final tax figure?", "calc": (4_800_000, {"rent": 600_000})},
        ],
    },
    {
        "id": "mt-03",
        "title": "relief discovery and actuarial follow-up",
        "language": "en",
        "turns": [
            {"user": "I'm a salaried employee earning NGN 6,000,000 a year. I rent a flat for NGN 2,400,000 a year and only make the mandatory pension contributions. What reliefs or deductions might I be missing?", "note": "Should surface rent relief (documentation), pension/VPC as an adjustable lever, and ask about mortgage/NHF/NHIS/life insurance without asserting they apply (constitution 5.1)."},
            {"user": "The voluntary pension sounds interesting. How do I set it up and what are the limits?", "note": "Should state: notify employer in writing, through employer into RSA, max one-third of monthly salary, once a month, 50/50 contingent/fixed, 2-year retention, 5-year tax rule (F-014)."},
            {"user": "If I put NGN 200,000 into voluntary pension this year, how much tax does that save me?", "counterfactual": (6_000_000, {}, "pension", 200_000)},
        ],
    },
    {
        "id": "mt-04",
        "title": "monthly-vs-annual clarification",
        "language": "en",
        "turns": [
            {"user": "I earn NGN 250,000. How much tax do I pay?", "note": "Should ask whether the figure is monthly or annual before computing (constitution 3.x)."},
            {"user": "That's per month. My annual figure is NGN 3,000,000.", "calc": (3_000_000, {})},
            {"user": "If I add NGN 100,000 of pension contributions, what happens to the tax?", "calc": (3_000_000, {"pension": 100_000})},
        ],
    },
    {
        "id": "mt-05",
        "title": "zero-band boundary",
        "language": "en",
        "turns": [
            {"user": "I earn NGN 800,000 a year. How much tax do I pay?", "calc": (800_000, {})},
            {"user": "What if I earn NGN 850,000 instead?", "calc": (850_000, {})},
            {"user": "And if I pay NGN 300,000 rent while earning 850,000?", "calc": (850_000, {"rent": 300_000})},
        ],
    },
    {
        "id": "mt-06",
        "title": "Pidgin conversation with relief follow-up",
        "language": "pcm",
        "turns": [
            {"user": "I dey earn NGN 120,000 every month. How much tax I go pay?", "calc": (1_440_000, {}), "note": "Must answer in Pidgin (constitution 8.1)."},
            {"user": "My rent na NGN 500,000 for a year. E go reduce my tax?", "calc": (1_440_000, {"rent": 500_000})},
            {"user": "So how much the rent relief take save me?", "counterfactual": (1_440_000, {}, "rent", 500_000), "note": "Answer stays in Pidgin."},
        ],
    },
    {
        "id": "mt-07",
        "title": "filing workflow and relief timing",
        "language": "en",
        "turns": [
            {"user": "My employer deducts PAYE from my salary every month. I just moved house and paid two years of rent. If I file the rent relief claim next month and it is approved later, does the relief apply from the month it is approved, or is it backdated?", "note": "Correct answer: tax is an annual liability and PAYE is instalments; the relief attaches to the year of assessment and over-deduction is settled by refund/credit (F-018), not by a month-by-month switch. Claims are made in the annual return (F-017)."},
            {"user": "Okay, so how and where do I actually submit the claim?", "note": "Should mention the annual return through the relevant state tax authority platform (LIRS e-Tax for Lagos), Tax Form A as the return of income and claims for reliefs, and evidence upload (F-017, F-012)."},
            {"user": "And if the PAYE deducted over the year turns out to be more than my final tax, what happens to the excess?", "note": "Refund after audit, payable within 90 days of the decision; set-off option; written refund claim within six years (F-018). Not a windfall - accurate claim required."},
        ],
    },
    {
        "id": "mt-08",
        "title": "savings coaching with rate math",
        "language": "en",
        "turns": [
            {"user": "I earn NGN 6,000,000 a year and I want to reduce my tax this year. What can I do?", "note": "Should present legal levers, leading with the flexible one (VPC), and mention documentation (constitution 5.x)."},
            {"user": "I can set aside NGN 50,000 every month for voluntary pension. How much tax would that save me?", "counterfactual": (6_000_000, {}, "pension", 600_000), "note": "600k/year within the one-third cap for a 6m salary; saving = 600k x 18% = 108,000."},
            {"user": "Is that better than claiming my 2.4m rent that I'm already paying?", "note": "Rent relief is a claim on money already spent and capped at 500,000; VPC is an adjustable additional saving. Both should be used; sequencing by impact (constitution 5.3)."},
        ],
    },
    {
        "id": "mt-09",
        "title": "scope boundaries then return to personal tax",
        "language": "en",
        "turns": [
            {"user": "How much tax does my company pay on its profits?", "note": "Out of scope: this is personal income tax guidance (constitution 4.x). Should decline clearly and briefly."},
            {"user": "What about VAT on the goods my shop sells?", "note": "Out of scope; decline. May note this model covers personal income tax for employees."},
            {"user": "Fine. Then how much tax do I personally pay on my NGN 5,000,000 salary?", "calc": (5_000_000, {})},
        ],
    },
    {
        "id": "mt-10",
        "title": "long-context accumulation",
        "language": "en",
        "turns": [
            {"user": "My gross annual salary is NGN 9,600,000.", "note": "Acknowledge and retain."},
            {"user": "I contribute NGN 800,000 to pension over the year.", "note": "Retain."},
            {"user": "I also pay NGN 2,400,000 rent annually.", "note": "Retain."},
            {"user": "By the way, can I deduct my children's school fees?", "note": "No - school fees are not in the eligible deductions list (F-003)."},
            {"user": "So what is my total tax for the year?", "calc": (9_600_000, {"pension": 800_000, "rent": 2_400_000}), "note": "Must use all accumulated facts: 9.6m gross, 800k pension, 480k rent relief."},
        ],
    },
]


def money(value) -> str:
    return format(value, ".2f")


def turn_truth(turn: dict, ruleset: dict) -> dict | None:
    if "calc" in turn:
        gross, reliefs = turn["calc"]
        result = calculate_full(gross, reliefs, ruleset)
        return {
            "kind": "calc",
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in reliefs.items()},
            },
            "expected_chargeable_income": money(result["chargeable_income"]),
            "expected_total_tax": money(result["total_tax"]),
        }
    if "counterfactual" in turn:
        gross, base_reliefs, field, new_value = turn["counterfactual"]
        result = run_counterfactual(gross, base_reliefs, field, new_value, ruleset)
        return {
            "kind": "counterfactual",
            "scenario_inputs": {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in base_reliefs.items()},
                "changed_field": field,
                "new_value": money(new_value),
            },
            "expected_chargeable_income": money(result["scenario_chargeable_income"]),
            "expected_total_tax": money(result["scenario_tax"]),
            "expected_savings": money(result["delta"]),
        }
    return None


def build_records() -> list[dict]:
    ruleset = load_ruleset()
    records = []
    for conv in CONVERSATIONS:
        turns = []
        for turn in conv["turns"]:
            built = {"user": turn["user"]}
            truth = turn_truth(turn, ruleset)
            if truth:
                built["ground_truth"] = truth
            if turn.get("note"):
                built["note"] = turn["note"]
            turns.append(built)
        records.append(
            {
                "id": conv["id"],
                "title": conv["title"],
                "language": conv["language"],
                "category": "multi_turn",
                "turns": turns,
            }
        )
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
        for turn in record["turns"]:
            if normalize(turn["user"]) in train_prompts:
                problems.append(f"overlap with training: {record['id']}")
    for record in records:
        if not (3 <= len(record["turns"]) <= 5):
            problems.append(f"{record['id']}: {len(record['turns'])} turns (want 3-5)")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "eval" / "multiturn_suite.jsonl")
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
        print(f"wrote {len(records)} conversations -> {args.out}")

    calc_turns = sum(
        1 for r in records for t in r["turns"] if "ground_truth" in t
    )
    total_turns = sum(len(r["turns"]) for r in records)
    print(f"verified: zero training overlap, turn counts valid")
    print(f"  conversations: {len(records)}, turns: {total_turns}, engine-scorable turns: {calc_turns}")


if __name__ == "__main__":
    main()
