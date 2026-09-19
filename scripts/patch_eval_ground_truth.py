#!/usr/bin/env python3
"""Add engine ground truth to the development probe's calculation records.

The baseline prompts were authored with natural-language figures; this script
maps the computable ones to engine scenarios and attaches scenario_inputs +
ground_truth in the same shape as the held-out probe, so stage comparisons
can score them. base-en-07 is intentionally skipped: its prompt references
"standard rent-relief deductions" without a rent figure, so no unique answer
exists.

Re-runnable: run after any edit to data/eval/baseline_prompts.jsonl.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset  # noqa: E402

PROMPTS = ROOT / "data" / "eval" / "baseline_prompts.jsonl"

# id -> (gross_annual, relief_inputs)
SCENARIOS: dict[str, tuple[int, dict]] = {
    "base-en-03": (800_000, {}),
    "base-en-04": (4_800_000, {"rent": 2_500_000}),
    "base-en-05": (3_000_000, {}),
    "base-en-06": (3_600_000, {"rent": 800_000}),
    "base-en-08": (3_000_000, {}),
    "base-en-09": (50_000_001, {}),
    "base-pcm-03": (1_200_000, {}),
    "base-pcm-04": (900_000, {"rent": 1_200_000}),
    "base-pcm-05": (25_000_000, {"pension": 240_000}),
}


def money(value) -> str:
    return format(value, ".2f")


def main() -> None:
    ruleset = load_ruleset()
    rows = [json.loads(line) for line in PROMPTS.read_text().splitlines() if line.strip()]
    patched = 0
    for row in rows:
        scenario = SCENARIOS.get(row["id"])
        if scenario is None:
            continue
        gross, reliefs = scenario
        result = calculate_full(gross, reliefs, ruleset)
        row["scenario_inputs"] = {
            "gross_annual_salary": money(gross),
            "relief_inputs": {k: money(v) for k, v in reliefs.items()},
        }
        row["ground_truth"] = {
            "expected_chargeable_income": money(result["chargeable_income"]),
            "expected_total_tax": money(result["total_tax"]),
        }
        patched += 1
        print(
            f"{row['id']}: gross {money(gross)} -> ci {money(result['chargeable_income'])}, "
            f"tax {money(result['total_tax'])}"
        )

    with open(PROMPTS, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\npatched {patched} records -> {PROMPTS}")
    print("skipped: base-en-07 (no rent figure in prompt; not uniquely computable)")


if __name__ == "__main__":
    main()
