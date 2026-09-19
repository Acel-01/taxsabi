#!/usr/bin/env python3
"""Build the held-out probe set — prompts never seen in any training data.

Used for cross-stage comparisons and the Gate 2 before/after provenance.
Calculation prompts carry engine-computed ground truth so the same file can
be used for scoring (stage gates) and behavior capture.

Run after any training-data change to re-verify zero overlap:
    uv run python scripts/build_heldout_probe.py --verify-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset  # noqa: E402


# Each entry: (id, language, category, prompt, scenario_inputs or None)
# scenario_inputs = (gross_annual_salary, relief_inputs) for calculation prompts.
PROMPTS = [
    ("probe-calc-01", "en", "calculation",
     "I earn NGN 1,450,000 a year and no deductions or reliefs. How much tax do I pay?",
     (1_450_000, {})),
    ("probe-calc-02", "en", "calculation",
     "I earn NGN 90,000 every month and no deductions. What's my annual tax?",
     (1_080_000, {})),
    ("probe-calc-03", "en", "calculation",
     "I earn NGN 5,750,000 a year and pay NGN 1,800,000 in rent. How much tax do I pay?",
     (5_750_000, {"rent": 1_800_000})),
    ("probe-calc-04", "en", "calculation",
     "I earn NGN 1,050,000 a year and contribute NGN 45,000 to pension. How much tax do I pay?",
     (1_050_000, {"pension": 45_000})),
    ("probe-calc-05", "en", "calculation",
     "What's my take-home pay if I earn NGN 2,100,000 a year with no deductions?",
     (2_100_000, {})),
    ("probe-calc-06", "en", "calculation",
     "I earn NGN 8,400,000 a year, contribute NGN 500,000 to pension and NGN 72,000 to NHIS. How much tax do I pay?",
     (8_400_000, {"pension": 500_000, "nhis": 72_000})),
    ("probe-calc-07", "en", "calculation",
     "I earn NGN 32,000,000 a year and pay NGN 900,000 in rent. How much tax do I pay?",
     (32_000_000, {"rent": 900_000})),
    ("probe-fact-01", "en", "statutory_fact",
     "How many tax bands apply to individuals in Nigeria in 2026, and what is each rate?",
     None),
    ("probe-fact-02", "en", "statutory_fact",
     "Is the rent deduction capped, and if so, at what amount?",
     None),
    ("probe-fact-03", "en", "statutory_fact",
     "Can I deduct my children's school fees from my taxable income?",
     None),
    ("probe-clar-01", "en", "clarification",
     "My salary is NGN 700,000. How much tax do I owe?",
     None),
    ("probe-scope-01", "en", "scope_behavior",
     "Do these personal income tax rules apply to a company director?",
     None),
    ("probe-scope-02", "en", "scope_behavior",
     "I'm a student with no income. Do I need to file tax?",
     None),
    ("probe-calc-08", "pcm", "calculation",
     "I dey earn 70k every month. How much tax I go pay?",
     (840_000, {})),
    ("probe-calc-09", "pcm", "calculation",
     "My rent na 600k a year. How much relief I fit get?",
     (600_000, {"rent": 600_000})),
    ("probe-fact-04", "pcm", "statutory_fact",
     "Wetin be the difference between pension and NHF contribution for tax?",
     None),
    ("probe-clar-02", "pcm", "clarification",
     "I dey contribute to pension. How much tax I go save?",
     None),
    ("probe-fact-05", "pcm", "statutory_fact",
     "The tax office need wetin as proof for my pension claim?",
     None),
    ("probe-scope-03", "pcm", "scope_behavior",
     "Abuja vs Lagos — any difference in tax?",
     None),
    ("probe-calc-10", "pcm", "calculation",
     "I earn NGN 2,700,000 a year and I pay 450k for rent. How much tax I go pay?",
     (2_700_000, {"rent": 450_000})),
]


def money(value) -> str:
    return format(value, ".2f")


def build_records() -> list[dict]:
    ruleset = load_ruleset()
    records = []
    for pid, lang, category, prompt, scenario in PROMPTS:
        record = {
            "id": pid,
            "language": lang,
            "category": category,
            "prompt": prompt,
        }
        if scenario is not None:
            gross, reliefs = scenario
            result = calculate_full(gross, reliefs, ruleset)
            record["scenario_inputs"] = {
                "gross_annual_salary": money(gross),
                "relief_inputs": {k: money(v) for k, v in reliefs.items()},
            }
            record["ground_truth"] = {
                "expected_chargeable_income": money(result["chargeable_income"]),
                "expected_total_tax": money(result["total_tax"]),
            }
        records.append(record)
    return records


def verify_zero_overlap(records: list[dict]) -> list[str]:
    """Check no probe prompt appears verbatim in any training file."""
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
                text = row.get(key)
                if text:
                    train_prompts.add(" ".join(text.lower().split()))
    for record in records:
        norm = " ".join(record["prompt"].lower().split())
        if norm in train_prompts:
            problems.append(record["id"])
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "eval" / "probe_prompts_heldout.jsonl")
    args = parser.parse_args()

    records = build_records()
    problems = verify_zero_overlap(records)

    if problems:
        print(f"FAIL: {len(problems)} prompts overlap training data: {problems}")
        sys.exit(1)

    if not args.verify_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"wrote {len(records)} held-out probe prompts -> {args.out}")

    print(f"zero-overlap verified across all training files ({len(records)} prompts)")
    calc = [r for r in records if "ground_truth" in r]
    print(f"  calculations with engine ground truth: {len(calc)}")


if __name__ == "__main__":
    main()
