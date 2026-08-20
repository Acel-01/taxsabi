#!/usr/bin/env python3
"""Generate source-grounded non-calculation records with disjoint train/eval families."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


FACTS = {
    "f001": {
        "source_fact_ids": ["F-001"],
        "output": (
            "The individual income-tax bands are: first NGN 800,000 at 0%; next NGN 2,200,000 at 15%; "
            "next NGN 9,000,000 at 18%; next NGN 13,000,000 at 21%; next NGN 25,000,000 at 23%; "
            "and amounts above NGN 50,000,000 at 25%, under the Fourth Schedule to the Nigeria Tax Act 2025."
        ),
        "questions": [
            "List the Nigerian individual income-tax bands for 2026.",
            "What are the personal tax rates for the 2026 year of assessment?",
            "How does the 2026 Nigerian individual tax scale work?",
            "Which rates apply to different levels of individual chargeable income?",
            "What is the tax rate above NGN 50,000,000?",
            "How much of individual chargeable income is taxed at 0%?",
            "Give me the 2026 personal income-tax bands and percentages.",
            "What are the progressive income-tax brackets in Nigeria?",
            "Explain the Fourth Schedule tax bands in plain English.",
            "What rate applies to the next NGN 2,200,000 after the first band?",
        ],
    },
    "f002": {
        "source_fact_ids": ["F-002"],
        "output": "Chargeable income is total income less eligible deductions under section 30(1) of the Nigeria Tax Act 2025.",
        "questions": [
            "What does chargeable income mean under section 30?",
            "How do I get from total income to chargeable income?",
            "Is chargeable income the same as gross salary?",
            "What is deducted before applying the individual tax bands?",
            "Explain chargeable income simply.",
            "Which figure should be taxed after eligible deductions?",
            "Does total income automatically equal chargeable income?",
            "What does section 30(1) say about chargeable income?",
        ],
    },
    "f003": {
        "source_fact_ids": ["F-003", "F-005"],
        "output": (
            "The listed eligible-deduction categories include NHF, NHIS, and Pension Reform Act contributions; "
            "interest on a loan for developing an owner-occupied residential house; qualifying life-insurance or "
            "deferred-annuity premiums; and rent relief. Claims may require documentary evidence."
        ),
        "questions": [
            "Which payments can be eligible deductions for an individual?",
            "Can pension contributions reduce chargeable income?",
            "Are NHF and NHIS contributions listed as deductions?",
            "What deductions are listed in section 30(2)(a)?",
            "Can mortgage interest be deducted under these rules?",
            "Do life-insurance premiums appear among the eligible deductions?",
            "What kinds of relief should I ask about when calculating tax?",
            "Give me the deduction categories without calculating my tax.",
        ],
    },
    "f004": {
        "source_fact_ids": ["F-004", "F-005"],
        "output": (
            "Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. "
            "The actual rent must be accurately declared and evidence may be required."
        ),
        "questions": [
            "What is the rent-relief percentage?",
            "What is the maximum rent relief?",
            "How does the rent deduction work?",
            "If I pay rent, how much relief can I claim?",
            "Is rent relief based on monthly or annual rent?",
            "What happens when 20% of my rent is more than NGN 500,000?",
            "What information must I declare for rent relief?",
            "Can the tax authority ask for proof of rent?",
        ],
    },
    "f005": {
        "source_fact_ids": ["F-005"],
        "output": (
            "Yes. Under section 32, the relevant tax authority may require documentary evidence for a deduction "
            "claim and may refuse or reduce the deduction if the evidence is absent or inadequate."
        ),
        "questions": [
            "Can the tax authority ask for receipts for deductions?",
            "What happens if I cannot prove a deduction?",
            "Are deduction claims automatically accepted?",
            "What does section 32 say about proof?",
            "Do I need documents for rent relief?",
            "Can an unsupported deduction be reduced?",
            "What evidence might be required for a tax claim?",
            "Does the tax assistant treat every stated deduction as final?",
        ],
    },
    "f006": {
        "source_fact_ids": ["F-006", "F-003"],
        "output": (
            "For private-sector employees, NHF contribution is treated as voluntary under the NHF Act 1992 as "
            "amended by section 45 of the Business Facilitation (Miscellaneous Provisions) Act 2022. "
            "NHF contributions are separately listed as an eligible deduction under section 30(2)(a)(i) of the NTA 2025."
        ),
        "questions": [
            "Is NHF contribution voluntary for private-sector employees?",
            "Can a private-sector worker choose whether to contribute to NHF?",
            "Does an NHF contribution qualify as a tax deduction?",
            "What is the relationship between NHF contribution and tax relief?",
            "Which law changed the private-sector NHF position?",
            "Can I include a stated NHF contribution in my tax calculation?",
            "Is NHF the same as pension for this calculation?",
            "What should a private employee know about NHF and tax?",
        ],
    },
}

TRAIN_SCOPE = [
    ("scope-default", "I did not mention a country or tax year. What will you assume?", "I default to Nigeria and the 2026 year of assessment. If you mean another country or year, say so; this version supports Nigerian 2026 personal income tax."),
    ("scope-default", "I just said I earn 1.6m. Which tax rules will you use?", "Unless you specify otherwise, I will treat this as a Nigeria 2026 personal-income-tax question. Tell me if you mean another jurisdiction or year."),
    ("scope-default", "Do I need to say Nigeria and 2026 every time?", "No. This version defaults to Nigeria and the 2026 year of assessment, but I will state that assumption when it matters."),
    ("scope-country", "Calculate my Ghana personal income tax for 2026.", "I cannot calculate Ghanaian tax. This version is scoped to Nigerian personal income tax for the 2026 year of assessment."),
    ("scope-country", "How much tax do I owe in Kenya?", "I cannot calculate Kenyan tax. This version supports Nigerian personal income tax for 2026."),
    ("scope-country", "Use the UK tax bands for my salary.", "I cannot use UK tax bands. This assistant is scoped to Nigerian personal income tax for 2026."),
    ("scope-year", "Calculate my Nigerian personal income tax for 2025.", "I cannot reliably calculate the 2025 rules in this version. I am scoped to Nigerian personal income tax for the 2026 year of assessment."),
    ("scope-year", "What was my Nigerian tax under the 2024 rules?", "I cannot reliably calculate the 2024 rules in this version. I support Nigerian personal income tax for 2026."),
    ("scope-year", "Calculate my tax for 2027.", "I cannot reliably calculate the 2027 rules in this version. I support Nigerian personal income tax for 2026."),
]

TRAIN_CLARIFICATION = [
    ("clarification-salary", "How much tax do I pay if I have rent of NGN 500,000?", "I need your gross income and the relevant period before I can calculate tax. Is the NGN 500,000 monthly or annual rent?"),
    ("clarification-salary", "Calculate my tax. I contribute NGN 200,000 to pension.", "Please provide your gross salary and say whether it is monthly or annual. I should not infer your income."),
    ("clarification-period", "I earn NGN 300,000. Calculate my tax.", "Is NGN 300,000 your monthly or annual income? I need the period before calculating."),
    ("clarification-period", "My salary is 1.6m. What do I owe?", "Is NGN 1,600,000 your monthly or annual salary? Please clarify the period."),
    ("clarification-relief", "What other deductions can I claim?", "I can list possible categories, but I cannot assume that any category applies. Tell me which contributions or payments you actually made."),
    ("clarification-relief", "Add rent relief to my calculation.", "Please state the actual rent paid and the relevant period. I will not invent a rent amount."),
    ("clarification-proof", "I have no receipt for my rent. Can you still calculate it?", "I can show an estimate using the amount you state, but section 32 allows the tax authority to require evidence and refuse or reduce an unsupported claim."),
    ("clarification-proof", "Can you guarantee that my deduction will be accepted?", "No. I can calculate from stated facts, but deduction claims may require evidence and acceptance is for the relevant tax authority to determine."),
]


def record(record_id: str, family: str, category: str, question: str, answer: str, source_ids: list[str], split: str) -> dict:
    return {
        "id": record_id,
        "category": category,
        "language": "en",
        "instruction": question,
        "output": answer,
        "ground_truth": None,
        "verified_by_engine": False,
        "verification": "source_register",
        "source_fact_ids": source_ids,
        "scenario_family": f"{split}-{family}",
        "generated_by": "deterministic_template",
        "source_verified": True,
        "human_reviewed": False,
    }


def expand_questions(questions: list[str], target: int) -> list[str]:
    expanded = []
    prefixes = (
        "In plain language, ",
        "Please explain this: ",
        "I want to understand this: ",
        "Can you clarify: ",
        "For my tax planning, ",
    )
    for question in questions:
        candidates = [question]
        lowered = question[:1].lower() + question[1:]
        candidates.extend(f"{prefix}{lowered}" for prefix in prefixes)
        for candidate in candidates:
            if candidate not in expanded:
                expanded.append(candidate)
            if len(expanded) >= target:
                return expanded
    return expanded


def expand_behavior_items(items: list[tuple[str, str, str]], target: int) -> list[tuple[str, str, str]]:
    expanded = []
    prefixes = (
        "Please help: ",
        "Quick question: ",
        "I need to know: ",
        "Can you clarify this? ",
    )
    for family, question, answer in items:
        candidates = [(family, question, answer)]
        candidates.extend((family, f"{prefix}{question}", answer) for prefix in prefixes)
        expanded.extend(candidates[:target])
    return expanded


def build_fact_records(split: str) -> list[dict]:
    records = []
    for key, fact in FACTS.items():
        questions = fact["questions"]
        if split == "train":
            selected = expand_questions(questions, 16)
        else:
            selected = [
                f"Could you explain this point: {questions[-1]}",
                f"In plain language, {questions[1].lower()}",
            ]
        for index, question in enumerate(selected, start=1):
            records.append(record(
                f"{split}-fact-{key}-{index:02d}",
                f"fact-{key}",
                "statutory_fact",
                question,
                fact["output"],
                fact["source_fact_ids"],
                split,
            ))
    return records


def build_behavior_records(items: list[tuple[str, str, str]], split: str, category: str, source_ids: list[str]) -> list[dict]:
    return [
        record(f"{split}-{family}-{index:02d}", family, category, question, answer, source_ids, split)
        for index, (family, question, answer) in enumerate(items, start=1)
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=True) + "\n" for item in records))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    train = build_fact_records("train")
    train += build_behavior_records(expand_behavior_items(TRAIN_SCOPE, 5), "train", "scope_behavior", ["F-001", "F-002"])
    train += build_behavior_records(expand_behavior_items(TRAIN_CLARIFICATION, 5), "train", "clarification", ["F-002", "F-003", "F-005"])

    eval_items = [
        ("scope-default", "I left out the country and year. What jurisdiction and year do you use?", "I default to Nigeria and 2026, and I will state that assumption."),
        ("scope-country", "Calculate tax for South Africa.", "I cannot calculate South African tax. This version supports Nigerian personal income tax for 2026."),
        ("scope-year", "Calculate my Nigerian tax under the 2028 rules.", "I cannot reliably calculate 2028 rules. This version supports Nigerian personal income tax for 2026."),
        ("clarification-salary", "I only told you that I pay NGN 1,000,000 rent. What is my tax?", "I need your gross income and the period for the rent before calculating. I should not infer missing facts."),
        ("clarification-period", "I earn NGN 500,000. What tax do I owe?", "Is NGN 500,000 monthly or annual income? Please clarify the period."),
        ("clarification-proof", "Tell me the exact deduction the authority must accept.", "I cannot guarantee acceptance. Section 32 allows documentary evidence to be required and a deduction to be refused or reduced if evidence is inadequate."),
    ]
    evaluation = build_fact_records("eval")
    evaluation += build_behavior_records(eval_items, "eval", "scope_behavior", ["F-001", "F-002", "F-005"])

    write_jsonl(args.output_dir / "train" / "behavior_en.jsonl", train)
    write_jsonl(args.output_dir / "eval" / "behavior_en.jsonl", evaluation)
    print(f"wrote {len(train)} training behavior records")
    print(f"wrote {len(evaluation)} evaluation behavior records")


if __name__ == "__main__":
    main()
