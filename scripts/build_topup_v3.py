#!/usr/bin/env python3
"""Build the SFT v3 top-up: targeted drills for the v2 held-out failures.

Clusters addressed (all amounts are NOVEL — they avoid the held-out probe):
  1. Rent relief percentage: many incomes x rents, below and above the cap.
  2. Band-slice arithmetic: incomes just inside/outside band boundaries.
  3. Clarification boundaries: ambiguous period -> ask; stated period -> compute.
  4. Fact corrections: school fees, pension vs NHF, Abuja vs Lagos, student
     filing, plus citation-bearing variants of the core facts.

Output: data/sft_jobs/topup_v3/batch_*.jsonl + README

Usage:
    uv run python scripts/build_topup_v3.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset, run_counterfactual  # noqa: E402

JOBS = ROOT / "data" / "sft_jobs" / "topup_v3"

# 1. Rent drills: (gross, rent). Rents below and above the NGN 500k cap.
RENT_DRILLS = [
    (1_620_000, 350_000), (2_340_000, 620_000), (3_180_000, 780_000),
    (4_250_000, 1_200_000), (6_750_000, 2_900_000), (9_300_000, 4_100_000),
    (2_050_000, 960_000), (5_400_000, 1_650_000), (11_200_000, 3_300_000),
    (1_980_000, 240_000), (3_760_000, 1_100_000), (7_800_000, 2_250_000),
    (14_500_000, 5_000_000), (2_880_000, 430_000), (4_620_000, 890_000),
]

# 2. Boundary drills: incomes just inside/outside band edges.
BOUNDARY_INCOMES = [
    799_999, 800_001, 1_310_000, 2_400_000, 3_050_000, 5_900_000,
    11_900_000, 12_100_000, 24_900_000, 25_100_000, 49_900_000, 50_100_000,
    3_150_000, 12_450_000, 25_750_000,
]

# 3. Clarify-ask: no period stated -> assistant must ask monthly vs annual.
CLARIFY_ASK = [
    (1_350_000, "en"), (750_000, "en"), (4_300_000, "en"),
    (2_050_000, "en"), (960_000, "en"), (6_100_000, "en"),
    (1_100_000, "pcm"), (3_400_000, "pcm"), (85_000, "pcm"),
    (2_600_000, "pcm"), (1_750_000, "pcm"), (5_300_000, "pcm"),
]

# 4. Facts targeted at the observed failures (and citation reinforcements).
FACTS = [
    {
        "id": "rent-cap",
        "subject": "that rent relief is 20% of annual rent, capped at NGN 500,000",
        "required_terms": ["20%", "500,000"],
        "source_fact_ids": ["F-004"],
        "citation": "section 30(2)(a)(vi) of the Nigeria Tax Act 2025",
    },
    {
        "id": "school-fees",
        "subject": "whether school fees are deductible",
        "required_terms": ["school fees", "not"],
        "source_fact_ids": ["F-003"],
    },
    {
        "id": "pension-vs-nhf",
        "subject": "the difference between pension and NHF contributions for tax",
        "required_terms": ["Pension Reform Act", "NHF"],
        "source_fact_ids": ["F-003", "F-006"],
    },
    {
        "id": "abuja-lagos",
        "subject": "whether tax rules differ between Abuja and Lagos",
        "required_terms": ["tax authority"],
        "source_fact_ids": ["F-008"],
    },
    {
        "id": "student",
        "subject": "whether a student with no income pays or files tax",
        "required_terms": ["no income", "annual return"],
        "source_fact_ids": ["F-013", "F-017"],
    },
    {
        "id": "bands",
        "subject": "the 2026 income tax bands",
        "required_terms": ["800,000", "0%", "15%", "18%", "21%", "23%", "25%"],
        "source_fact_ids": ["F-001"],
        "citation": "the Fourth Schedule to the Nigeria Tax Act 2025",
    },
    {
        "id": "paye",
        "subject": "the PAYE remittance deadline",
        "required_terms": ["10th"],
        "source_fact_ids": ["F-011"],
    },
    {
        "id": "refund",
        "subject": "how overpaid tax is refunded",
        "required_terms": ["90 days", "six years"],
        "source_fact_ids": ["F-018"],
    },
    {
        "id": "vpc",
        "subject": "the voluntary pension contribution limits",
        "required_terms": ["one-third", "writing", "employer"],
        "source_fact_ids": ["F-014"],
    },
    {
        "id": "evidence",
        "subject": "what evidence a deduction claim needs",
        "required_terms": ["writing", "documentary evidence"],
        "source_fact_ids": ["F-005", "F-012"],
    },
]

USER_TEXT_OVERRIDES = {
    "tu3-fact-school-fees-00": "Are school fees an eligible deduction for personal income tax?",
    "tu3-fact-student-00": "If someone has no income at all, do they still need to file a tax return?",
    "tu3-fact-pcm-pension-vs-nhf-00": "Pension and NHF money - wetin be the difference when dem dey calculate tax?",
    "tu3-fact-pension-vs-nhf-00": "Pension contributions and NHF contributions both reduce tax - so what actually separates them?",
}

FACT_STYLES = [
    ("direct", "ask the question directly"),
    ("verify", "say someone told them the opposite and ask if that is right"),
    ("context", "add a one-line personal context before asking"),
    ("cited", "ask for the exact legal provision alongside the answer"),
]


def money(value) -> str:
    return format(value, ".2f")


def calc_blueprint(pid: str, gross: int, reliefs: dict, ruleset: dict, language: str = "en",
                   guidance: str | None = None) -> dict:
    result = calculate_full(gross, reliefs, ruleset)
    breakdown = [
        {"band": b["band"], "rate": format(b["rate"], ".2f"),
         "taxed_amount": format(b["taxed_amount"], ".2f"), "tax": format(b["tax"], ".2f")}
        for b in result["breakdown"]
    ]
    relief_text = ", ".join(f"{money(v)} for {k}" for k, v in reliefs.items()) or "none"
    return {
        "conversation_id": pid,
        "type": "single_calc",
        "language": language,
        "style": "drill",
        "turns": [{
            "role": "user",
            "guidance": guidance or (
                f"state the salary and these payments: {relief_text}; the period is explicitly stated "
                "(a year or every month, matching the amounts); ask for the tax"
            ),
        }],
        "authoritative": {
            "gross_annual_salary": money(gross),
            "relief_inputs": {k: money(v) for k, v in reliefs.items()},
            "applied_reliefs": {k: money(v) for k, v in reliefs.items()},
            "total_relief": money(result["total_relief"]),
            "chargeable_income": money(result["chargeable_income"]),
            "total_tax": money(result["total_tax"]),
            "tax_breakdown": breakdown,
        },
        "source_fact_ids": ["F-001", "F-002", "F-004"],
        "scenario_id": "topup-v3",
        "scenario_family": "topup_drill",
    }


def clarify_ask_blueprint(pid: str, amount: int, language: str) -> dict:
    return {
        "conversation_id": pid,
        "type": "clarify_ask",
        "language": language,
        "style": "clarify",
        "turns": [{
            "role": "user",
            "guidance": (
                f"give the amount {amount} WITHOUT saying whether it is monthly or annual, "
                "then ask for the tax; the assistant must ask for the period instead of computing"
            ),
        }],
        "authoritative": {"stated_amount": money(amount)},
        "required_terms": ["monthly", "annual"],
        "source_fact_ids": ["F-002"],
        "scenario_id": "topup-v3",
        "scenario_family": "topup_clarify",
    }


def cf_blueprint(pid: str, gross: int, rent: int, ruleset: dict, language: str) -> dict:
    result = run_counterfactual(gross, {}, "rent", rent, ruleset)
    base = calculate_full(gross, {}, ruleset)
    base_applied = {}
    return {
        "conversation_id": pid,
        "type": "single_counterfactual",
        "language": language,
        "style": "drill",
        "turns": [{
            "role": "user",
            "guidance": (
                f"state the salary {money(gross)} and that they pay rent of {money(rent)} a year; "
                "ask how much tax the rent relief saves"
            ),
        }],
        "authoritative": {
            "gross_annual_salary": money(gross),
            "base_relief_inputs": base_applied,
            "base_chargeable_income": money(base["chargeable_income"]),
            "base_tax": money(base["total_tax"]),
            "changed_field": "rent",
            "new_value": money(rent),
            "extra_amount": money(rent),
            "scenario_chargeable_income": money(result["scenario_chargeable_income"]),
            "scenario_tax": money(result["scenario_tax"]),
            "tax_saving": money(result["delta"]),
        },
        "source_fact_ids": ["F-001", "F-002", "F-004"],
        "scenario_id": "topup-v3",
        "scenario_family": "topup_counterfactual",
    }


def fact_blueprint(pid: str, fact: dict, style: tuple[str, str], language: str) -> dict:
    terms = list(fact["required_terms"])
    if style[0] == "cited" and fact.get("citation"):
        terms.append(fact["citation"])
    turns = [{
        "role": "user",
        "guidance": f"{style[1]}; the question is about {fact['subject']}"
                    + ("; the answer must cite the exact legal provision" if style[0] == "cited" else ""),
    }]
    if pid in USER_TEXT_OVERRIDES:
        turns[0]["user_text"] = USER_TEXT_OVERRIDES[pid]
        turns[0]["guidance"] = "use the exact user question text in user_text"
    record = {
        "conversation_id": pid,
        "type": "single_fact",
        "language": language,
        "style": style[0],
        "turns": turns,
        "authoritative": {"citation": fact["citation"]} if style[0] == "cited" and fact.get("citation") else {},
        "required_terms": terms,
        "source_fact_ids": fact["source_fact_ids"],
        "scenario_id": "topup-v3",
        "scenario_family": "topup_fact",
    }
    return record


INSTRUCTIONS = """# Top-up v3 — targeted drills

Single-turn records (2 turns each: one user question, one assistant answer). Follow `data/sft_jobs/single_en/README.md` rules.

Answer format (working first, total LAST):
- single_calc: "Gross income: NGN G. Reliefs applied: ... total relief NGN R. Chargeable income: NGN C. Band breakdown: ... Total tax: NGN X."
- single_counterfactual: "Your tax drops from NGN A to NGN B. [one-line reason] Saving: NGN S."
- clarify_ask: the assistant must ASK whether the amount is monthly or annual (the required terms "monthly" and "annual" must both appear); do NOT compute.
- single_fact: concise answer; every `required_terms` string must appear verbatim; no invented figures.

If a blueprint has `user_text`, the user question must be exactly that text (no rewording).
Number discipline: use ONLY values from the blueprint `authoritative` block; never invent/recalculate/round. For single_calc, apply the rent relief rule exactly as the engine did (20% of rent, capped at NGN 500,000) - never deduct the full rent unless the applied relief equals it. Amount format "NGN 3,000,000".

Method: temporary Python script via heredoc defining question and answer per conversation_id, merging blueprint fields (id from conversation_id, type, language, authoritative, required_terms, source_fact_ids, scenario_id, scenario_family) + generated_by "opencode". Pidgin records must be natural Nigerian Pidgin.

Do not modify other files. Do not run scripts/verify_sft_generation.py. Return one line per batch.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()

    ruleset = load_ruleset()
    items: list[dict] = []

    for i, (gross, rent) in enumerate(RENT_DRILLS):
        items.append(calc_blueprint(f"tu3-rent-{i:04d}", gross, {"rent": rent}, ruleset))
    for i, gross in enumerate(BOUNDARY_INCOMES):
        items.append(calc_blueprint(f"tu3-bound-{i:04d}", gross, {}, ruleset))
    for i, (amount, language) in enumerate(CLARIFY_ASK):
        items.append(clarify_ask_blueprint(f"tu3-clar-{i:04d}", amount, language))
    for i, (gross, rent) in enumerate(RENT_DRILLS[:8]):
        items.append(cf_blueprint(f"tu3-cf-{i:04d}", gross, rent, ruleset, "en"))
    for i, (gross, rent) in enumerate(RENT_DRILLS[8:12]):
        items.append(cf_blueprint(f"tu3-cf-pcm-{i:04d}", gross, rent, ruleset, "pcm"))
    for i, fact in enumerate(FACTS):
        styles = FACT_STYLES if fact["id"] in ("school-fees", "pension-vs-nhf", "abuja-lagos", "student") else FACT_STYLES[:2]
        for j, style in enumerate(styles):
            items.append(fact_blueprint(f"tu3-fact-{fact['id']}-{j:02d}", fact, style, "en"))
    # Pidgin fact reinforcements for the failure topics
    for i, fact in enumerate(FACTS[:4]):
        items.append(fact_blueprint(f"tu3-fact-pcm-{fact['id']}-00", fact, FACT_STYLES[0], "pcm"))
    # Pidgin rent drills
    for i, (gross, rent) in enumerate(RENT_DRILLS[:8]):
        items.append(calc_blueprint(f"tu3-rent-pcm-{i:04d}", gross, {"rent": rent}, ruleset, language="pcm"))

    if JOBS.exists():
        shutil.rmtree(JOBS)
    JOBS.mkdir(parents=True)
    (JOBS / "README.md").write_text(INSTRUCTIONS)
    batches = [items[i:i + args.batch_size] for i in range(0, len(items), args.batch_size)]
    for n, batch in enumerate(batches, 1):
        with open(JOBS / f"batch_{n:03d}.jsonl", "w") as fh:
            for item in batch:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    lang_counts = {"en": 0, "pcm": 0}
    type_counts: dict[str, int] = {}
    for item in items:
        lang_counts[item["language"]] += 1
        type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1
    print(f"wrote {len(items)} top-up items in {len(batches)} batches -> {JOBS}")
    print(f"languages: {lang_counts}")
    print(f"types: {type_counts}")


if __name__ == "__main__":
    main()
