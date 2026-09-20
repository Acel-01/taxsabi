#!/usr/bin/env python3
"""Build SFT conversation generation jobs, batched for model-by-layer runs.

Emits self-contained job files that any language model (via opencode sessions
or an API) can process: each blueprint carries the exact engine-computed
values the assistant turns must use. Outputs are verified afterwards by
scripts/verify_sft_generation.py.

Layers:
  layer_a  English, non-coaching       (bulk: ~300 conversations)
  layer_b  English, coaching           (~80)
  layer_c  Pidgin, core types          (~120, human-reviewed)

Usage:
    uv run python scripts/build_sft_jobs.py
    uv run python scripts/build_sft_jobs.py --batch-size 10 --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset, money, run_counterfactual  # noqa: E402

SCENARIOS = ROOT / "data" / "scenarios"
JOBS = ROOT / "data" / "sft_jobs"

# Fact/procedure blueprints: content the assistant must state (checked by term).
FACT_BLUEPRINTS = [
    {
        "id": "fact-bands",
        "user": "answer the question about the 2026 personal income tax bands and rates",
        "required_terms": ["800,000", "0%", "15%", "18%", "21%", "23%", "25%"],
        "source_fact_ids": ["F-001"],
    },
    {
        "id": "fact-rent",
        "user": "explain the rent relief rule, including the cap",
        "required_terms": ["20%", "500,000"],
        "source_fact_ids": ["F-004"],
    },
    {
        "id": "fact-minwage",
        "user": "explain the minimum wage exemption",
        "required_terms": ["70,000", "exempt"],
        "source_fact_ids": ["F-009", "F-015"],
    },
    {
        "id": "fact-paye",
        "user": "state when PAYE must be remitted and the employer annual return deadline",
        "required_terms": ["10th", "31 January"],
        "source_fact_ids": ["F-011"],
    },
    {
        "id": "fact-pension",
        "user": "state the mandatory pension contribution rates",
        "required_terms": ["10%", "8%"],
        "source_fact_ids": ["F-014"],
    },
    {
        "id": "fact-vpc",
        "user": "explain the voluntary pension contribution limits and channel",
        "required_terms": ["one-third", "writing", "employer"],
        "source_fact_ids": ["F-014"],
    },
    {
        "id": "fact-filing",
        "user": "explain where and how relief claims are filed",
        "required_terms": ["annual return", "written"],
        "source_fact_ids": ["F-017"],
    },
    {
        "id": "fact-refund",
        "user": "explain how overpaid tax is refunded and the timelines",
        "required_terms": ["90 days", "six years"],
        "source_fact_ids": ["F-018"],
    },
]

SCOPE_BLUEPRINTS = [
    "ask whether the assistant can prepare and file a company's annual tax return",
    "ask for help computing the VAT the shop must remit",
    "ask about capital gains tax on selling shares",
    "ask for tax advice about a business in Ghana",
]

COACHING_DISCOVERY = [
    "describe a salaried employee who rents and never claims anything, ask what reliefs may be missed",
    "describe a pay raise and ask how to keep more of it",
    "describe spare monthly savings and ask how to use them tax-efficiently",
]


def load_scenarios() -> tuple[list[dict], list[dict]]:
    calcs = [json.loads(line) for line in (SCENARIOS / "train.jsonl").read_text().splitlines() if line.strip()]
    counterfactuals = [
        json.loads(line)
        for line in (SCENARIOS / "counterfactual_train.jsonl").read_text().splitlines()
        if line.strip()
    ]
    return calcs, counterfactuals


def gt_block(scenario: dict) -> dict:
    gt = scenario["ground_truth"]
    return {
        "gross_annual_salary": gt["gross_annual_salary"],
        "relief_inputs": gt.get("relief_inputs", {}),
        "applied_reliefs": gt.get("applied_reliefs", {}),
        "total_relief": gt.get("total_relief", "0.00"),
        "chargeable_income": gt["expected_chargeable_income"],
        "total_tax": gt["expected_total_tax"],
        "tax_breakdown": gt.get("tax_breakdown", []),
    }


def calc_block(gross, reliefs, ruleset) -> dict:
    result = calculate_full(gross, reliefs, ruleset)
    breakdown = [
        {
            "band": entry["band"],
            "rate": format(entry["rate"], ".2f"),
            "taxed_amount": format(entry["taxed_amount"], ".2f"),
            "tax": format(entry["tax"], ".2f"),
        }
        for entry in result["breakdown"]
    ]
    return {
        "gross_annual_salary": format(result["gross_annual"], ".2f"),
        "relief_inputs": {k: format(v, ".2f") for k, v in reliefs.items()},
        "applied_reliefs": {k: format(v, ".2f") for k, v in reliefs.items()},
        "total_relief": format(result["total_relief"], ".2f"),
        "chargeable_income": format(result["chargeable_income"], ".2f"),
        "total_tax": format(result["total_tax"], ".2f"),
        "tax_breakdown": breakdown,
    }


def base_facts_phrase(base_reliefs: dict) -> str:
    if not base_reliefs:
        return ""
    listing = ", ".join(f"{format(v, '.2f')} for {k}" for k, v in base_reliefs.items())
    return f" and these current payments: {listing}"


def change_phrase(field: str, new_value: float, base_reliefs: dict) -> str:
    if field in base_reliefs:
        current = format(base_reliefs[field], ".2f")
        return f"increasing their {field} to {new_value} (currently {current})"
    return f"adding {new_value} of {field}"


def extra_amount(field: str, new_value: float, base_reliefs: dict) -> float:
    if field in base_reliefs:
        return round(new_value - base_reliefs[field], 2)
    return new_value


def build_accumulate(calcs: list[dict], rng: random.Random, count: int) -> list[dict]:
    blueprints = []
    for i in range(count):
        scenario = calcs[i % len(calcs)]
        gt = gt_block(scenario)
        reliefs = list(gt["relief_inputs"].items())
        turns = [
            {
                "role": "user",
                "guidance": "state the annual salary as a plain fact, without asking for a calculation yet",
            }
        ]
        if len(reliefs) == 1:
            name, amount = reliefs[0]
            turns.append(
                {
                    "role": "user",
                    "guidance": f"mention paying {amount} for {name} this year; still no calculation request",
                }
            )
        elif len(reliefs) >= 2:
            listing = ", ".join(f"{amount} for {name}" for name, amount in reliefs)
            turns.append(
                {
                    "role": "user",
                    "guidance": f"mention these payments in one message: {listing}; still no calculation request",
                }
            )
        else:
            turns.append(
                {"role": "user", "guidance": "add one personal detail that does not change the tax facts"}
            )
        turns.append(
            {
                "role": "user",
                "guidance": "now ask for the total tax for the year; the assistant computes using all facts stated",
            }
        )
        blueprints.append(
            {
                "conversation_id": f"sft-a-ath-{i:04d}",
                "type": "accumulate_compute",
                "turns": turns,
                "authoritative": gt,
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_counterfactual(cf: list[dict], rng: random.Random, count: int) -> list[dict]:
    blueprints = []
    for i in range(count):
        scenario = cf[i % len(cf)]
        gt = scenario["ground_truth"]
        field = gt["changed_field"]
        new_value = gt.get(f"new_{field}") or gt.get("new_value")
        base_gross = float(gt["gross_annual_salary"])
        base_reliefs = {k: float(v) for k, v in gt.get("base_relief_inputs", {}).items()}
        authoritative = {
            "gross_annual_salary": gt["gross_annual_salary"],
            "base_relief_inputs": gt.get("base_relief_inputs", {}),
            "base_chargeable_income": gt["base_chargeable_income"],
            "base_tax": gt["base_tax"],
            "scenario_chargeable_income": gt["scenario_chargeable_income"],
            "scenario_tax": gt["scenario_tax"],
            "tax_saving": gt["tax_saving"],
            "changed_field": field,
            "new_value": format(float(new_value), ".2f"),
            "extra_amount": format(extra_amount(field, float(new_value), base_reliefs), ".2f"),
        }
        turns = [
            {
                "role": "user",
                "guidance": "state salary" + base_facts_phrase(base_reliefs) + ", then ask for the tax",
            },
            {
                "role": "user",
                "guidance": (
                    f"ask what happens to the tax if {change_phrase(field, float(new_value), base_reliefs)}; "
                    "the assistant shows both taxes and the saving"
                ),
            },
        ]
        blueprints.append(
            {
                "conversation_id": f"sft-a-cf-{i:04d}",
                "type": "counterfactual",
                "turns": turns,
                "authoritative": authoritative,
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_correction(calcs: list[dict], rng: random.Random, count: int, ruleset: dict) -> list[dict]:
    blueprints = []
    start = len(calcs) // 2
    for i in range(count):
        scenario = calcs[(start + i) % len(calcs)]
        gross = float(scenario["ground_truth"]["gross_annual_salary"])
        reliefs = {k: float(v) for k, v in scenario["ground_truth"].get("relief_inputs", {}).items()}
        original = calc_block(gross, reliefs, ruleset)
        delta = rng.choice([300_000, 500_000, 750_000, 1_000_000])
        corrected_gross = gross + delta
        corrected = calc_block(corrected_gross, reliefs, ruleset)
        turns = [
            {"role": "user", "guidance": "state the original salary and ask for the tax"},
            {
                "role": "user",
                "guidance": f"correct the salary upward by {delta} (say the original figure was a mistake), then ask for the new tax",
            },
        ]
        blueprints.append(
            {
                "conversation_id": f"sft-a-corr-{i:04d}",
                "type": "correction",
                "turns": turns,
                "authoritative": {"original": original, "corrected": corrected},
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_clarify(calcs: list[dict], rng: random.Random, count: int, ruleset: dict) -> list[dict]:
    monthly = [s for s in calcs if s.get("presentation", {}).get("salary_period") == "monthly"]
    blueprints = []
    for i in range(count):
        scenario = monthly[i % len(monthly)] if monthly else calcs[i % len(calcs)]
        annual_gross = float(scenario["ground_truth"]["gross_annual_salary"])
        monthly_amount = annual_gross / 12
        reliefs = {k: float(v) for k, v in scenario["ground_truth"].get("relief_inputs", {}).items()}
        authoritative = calc_block(annual_gross, reliefs, ruleset)
        turns = [
            {
                "role": "user",
                "guidance": f"give the figure {monthly_amount:.0f} without saying whether it is monthly or annual, then ask for the tax; the assistant must ask for the period instead of computing",
            },
            {
                "role": "user",
                "guidance": "clarify that the figure is the monthly salary, then the assistant computes using the annual amount",
            },
        ]
        blueprints.append(
            {
                "conversation_id": f"sft-a-clar-{i:04d}",
                "type": "clarify_compute",
                "turns": turns,
                "authoritative": {"monthly_amount": format(monthly_amount, ".2f"), **authoritative},
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_topic_shift(calcs: list[dict], facts: list[dict], rng: random.Random, count: int) -> list[dict]:
    blueprints = []
    offset = len(calcs) // 3
    for i in range(count):
        scenario = calcs[(offset + i) % len(calcs)]
        fact = facts[i % len(facts)]
        gt = gt_block(scenario)
        turns = [
            {"role": "user", "guidance": "ask for the tax on the stated salary"},
            {"role": "user", "guidance": f"change topic: {fact['user']}"},
            {
                "role": "user",
                "guidance": "return to the first topic and ask the assistant to restate the tax figure it gave",
            },
        ]
        blueprints.append(
            {
                "conversation_id": f"sft-a-shift-{i:04d}",
                "type": "topic_shift",
                "turns": turns,
                "authoritative": gt,
                "required_terms": fact["required_terms"],
                "source_fact_ids": scenario.get("source_fact_ids", []) + fact["source_fact_ids"],
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_scope(calcs: list[dict], rng: random.Random, count: int) -> list[dict]:
    blueprints = []
    offset = len(calcs) // 4
    for i in range(count):
        scenario = calcs[(offset + i) % len(calcs)]
        out_scope = SCOPE_BLUEPRINTS[i % len(SCOPE_BLUEPRINTS)]
        gt = gt_block(scenario)
        turns = [
            {"role": "user", "guidance": f"{out_scope}; the assistant must decline briefly and say what it covers"},
            {"role": "user", "guidance": "ask the in-scope personal income tax question for the stated salary"},
        ]
        blueprints.append(
            {
                "conversation_id": f"sft-a-scope-{i:04d}",
                "type": "scope_decline",
                "turns": turns,
                "authoritative": gt,
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return blueprints


def build_coaching(cf: list[dict], facts: list[dict], rng: random.Random, count: int, ruleset: dict) -> list[dict]:
    blueprints = []
    for i in range(count):
        kind = ["discovery", "savings", "sequencing"][i % 3]
        if kind == "discovery":
            scenario = cf[(i * 3) % len(cf)]
            gt = scenario["ground_truth"]
            field = gt["changed_field"]
            new_value = float(gt.get(f"new_{field}") or gt.get("new_value"))
            base_gross = float(gt["gross_annual_salary"])
            base_reliefs = {k: float(v) for k, v in gt.get("base_relief_inputs", {}).items()}
            cf_result = run_counterfactual(base_gross, base_reliefs, field, new_value, ruleset)
            base_calc = calculate_full(base_gross, base_reliefs, ruleset)
            discovery = COACHING_DISCOVERY[i % len(COACHING_DISCOVERY)]
            turns = [
                {"role": "user", "guidance": f"{discovery}; the assistant asks questions rather than asserting reliefs apply"},
                {
                    "role": "user",
                    "guidance": f"confirm they will {change_phrase(field, new_value, base_reliefs)}, then ask how much tax it saves",
                },
            ]
            blueprints.append(
                {
                    "conversation_id": f"sft-b-disc-{i:04d}",
                    "type": "coaching_discovery",
                    "turns": turns,
                    "authoritative": {
                        "gross_annual_salary": format(base_gross, ".2f"),
                        "base_relief_inputs": {k: format(v, ".2f") for k, v in base_reliefs.items()},
                        "base_chargeable_income": format(base_calc["chargeable_income"], ".2f"),
                        "base_tax": format(cf_result["base_tax"], ".2f"),
                        "changed_field": field,
                        "new_value": format(new_value, ".2f"),
                        "extra_amount": format(extra_amount(field, new_value, base_reliefs), ".2f"),
                        "scenario_chargeable_income": format(cf_result["scenario_chargeable_income"], ".2f"),
                        "scenario_tax": format(cf_result["scenario_tax"], ".2f"),
                        "tax_saving": format(cf_result["delta"], ".2f"),
                    },
                    "source_fact_ids": scenario.get("source_fact_ids", []),
                    "scenario_id": scenario["scenario_id"],
                    "scenario_family": scenario.get("scenario_family"),
                }
            )
        elif kind == "savings":
            scenario = cf[(i * 5 + 1) % len(cf)]
            gt = scenario["ground_truth"]
            field = gt["changed_field"]
            new_value = float(gt.get(f"new_{field}") or gt.get("new_value"))
            base_reliefs = {k: float(v) for k, v in gt.get("base_relief_inputs", {}).items()}
            turns = [
                {
                    "role": "user",
                    "guidance": (
                        "state salary" + base_facts_phrase(base_reliefs)
                        + f", then ask how much tax they would save by {change_phrase(field, new_value, base_reliefs)}"
                    ),
                },
                {"role": "user", "guidance": "ask whether there is a limit on that kind of contribution"},
            ]
            vpc_fact = facts[5]
            blueprints.append(
                {
                    "conversation_id": f"sft-b-save-{i:04d}",
                    "type": "coaching_savings",
                    "turns": turns,
                    "authoritative": {
                        "gross_annual_salary": gt["gross_annual_salary"],
                        "base_relief_inputs": gt.get("base_relief_inputs", {}),
                        "base_chargeable_income": gt["base_chargeable_income"],
                        "base_tax": gt["base_tax"],
                        "scenario_chargeable_income": gt["scenario_chargeable_income"],
                        "scenario_tax": gt["scenario_tax"],
                        "tax_saving": gt["tax_saving"],
                        "changed_field": field,
                        "new_value": format(new_value, ".2f"),
                        "extra_amount": format(extra_amount(field, new_value, base_reliefs), ".2f"),
                    },
                    "required_terms": vpc_fact["required_terms"],
                    "source_fact_ids": scenario.get("source_fact_ids", []) + vpc_fact["source_fact_ids"],
                    "scenario_id": scenario["scenario_id"],
                    "scenario_family": scenario.get("scenario_family"),
                }
            )
        else:
            scenario = cf[(i * 7 + 2) % len(cf)]
            gt = scenario["ground_truth"]
            field = gt["changed_field"]
            new_value = float(gt.get(f"new_{field}") or gt.get("new_value"))
            base_gross = float(gt["gross_annual_salary"])
            base_reliefs = {k: float(v) for k, v in gt.get("base_relief_inputs", {}).items()}
            cf_result = run_counterfactual(base_gross, base_reliefs, field, new_value, ruleset)
            base_calc = calculate_full(base_gross, base_reliefs, ruleset)
            turns = [
                {"role": "user", "guidance": "describe spare savings and ask what to prioritise for tax purposes"},
                {"role": "user", "guidance": "ask how to set up the voluntary pension lever the assistant recommends"},
                {
                    "role": "user",
                    "guidance": f"ask how much tax they save by {change_phrase(field, new_value, base_reliefs)}",
                },
            ]
            blueprints.append(
                {
                    "conversation_id": f"sft-b-seq-{i:04d}",
                    "type": "coaching_sequencing",
                    "turns": turns,
                    "authoritative": {
                        "gross_annual_salary": format(base_gross, ".2f"),
                        "base_relief_inputs": {k: format(v, ".2f") for k, v in base_reliefs.items()},
                        "base_chargeable_income": format(base_calc["chargeable_income"], ".2f"),
                        "base_tax": format(cf_result["base_tax"], ".2f"),
                        "changed_field": field,
                        "new_value": format(new_value, ".2f"),
                        "extra_amount": format(extra_amount(field, new_value, base_reliefs), ".2f"),
                        "scenario_chargeable_income": format(cf_result["scenario_chargeable_income"], ".2f"),
                        "scenario_tax": format(cf_result["scenario_tax"], ".2f"),
                        "tax_saving": format(cf_result["delta"], ".2f"),
                    },
                    "source_fact_ids": scenario.get("source_fact_ids", []),
                    "scenario_id": scenario["scenario_id"],
                    "scenario_family": scenario.get("scenario_family"),
                }
            )
    return blueprints


def write_layer(layer: str, blueprints: list[dict], batch_size: int, instructions: str) -> int:
    layer_dir = JOBS / layer
    if layer_dir.exists():
        shutil.rmtree(layer_dir)
    layer_dir.mkdir(parents=True)
    (layer_dir / "README.md").write_text(instructions)
    batches = [blueprints[i : i + batch_size] for i in range(0, len(blueprints), batch_size)]
    for n, batch in enumerate(batches, 1):
        path = layer_dir / f"batch_{n:03d}.jsonl"
        with open(path, "w") as fh:
            for blueprint in batch:
                fh.write(json.dumps(blueprint, ensure_ascii=False) + "\n")
    return len(batches)


LAYER_A_INSTRUCTIONS = """# Layer A — English conversations (bulk)

Process every `batch_*.jsonl` in this folder, one batch at a time. For each blueprint, write a natural 3–5 turn conversation (user/assistant alternating, starting with user).

Rules:
- The `authoritative` values are computed by the local tax engine. Never change, round, or recalculate a number. Every amount the assistant states must come from the authoritative block (including tax breakdown values when shown).
- Follow the answer format: for a calculation, show the working first and the total LAST: "Gross income: ... Reliefs applied: ... Chargeable income: ... Band breakdown: ... Total tax: NGN X." For a what-if end with the saving: "Your tax drops from NGN A to NGN B. [one-line reason] Saving: NGN Y."
- `authoritative.tax_breakdown` entries give band, rate, taxed amount, and tax; use them for the band breakdown.
- Keep answers concise (roughly under 250 tokens). No preamble, no "Assuming Nigeria..." when the user already stated facts. Cite sections only where a specific legal claim is made.
- Types: accumulate_compute (facts build across turns, then calculate), counterfactual (show base tax, scenario tax, saving), correction (use the corrected figure immediately), clarify_compute (ask for the period before computing), topic_shift (retain facts across topic changes), scope_decline (decline out-of-scope briefly, then answer the in-scope question).
- If a blueprint has `required_terms`, the assistant text must state them (e.g. contribution rates, deadlines, caps).

Output: `data/sft_generated/layer_a/batch_NNN.jsonl`, same base name as the input file, one JSON object per line:

{"id": "<conversation_id>", "type": "<type>", "language": "en", "turns": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}], "authoritative": <copy of the blueprint authoritative block>, "source_fact_ids": [...], "scenario_id": "...", "scenario_family": "...", "generated_by": "opencode"}

JSONL only. No markdown fences. No commentary outside the JSON lines.
"""

LAYER_B_INSTRUCTIONS = """# Layer B — English coaching conversations

Process every `batch_*.jsonl` one at a time. These teach the coach behaviours: relief discovery (ask, don't assert), savings math at the user's marginal rate, and sequencing by impact.

Rules:
- Same arithmetic discipline as Layer A: every amount the assistant states comes from the `authoritative` block; never recalculate.
- For savings, state both taxes first and end with the saving: "Your tax falls from NGN A to NGN B. [one-line marginal reason] Saving: NGN X."
- Explain briefly why the saving is that size (marginal band), without dumping the full band table.
- Mention documentation requirements in one clause when recommending a claim or contribution.
- `required_terms` must appear where specified (contribution limits, channel, deadlines).
- Tone: direct, practical, legal optimisation, never evasion.

Output: `data/sft_generated/layer_b/batch_NNN.jsonl` with the same object shape as Layer A, language "en".
"""

LAYER_C_INSTRUCTIONS = """# Layer C — Pidgin conversations

Process every `batch_*.jsonl` one at a time. Same rules as Layer A, but write the conversation in natural Nigerian Pidgin.

Rules:
- Pidgin must sound like a Nigerian person explaining tax, not English with Pidgin words sprinkled in. Keep the conversation in Pidgin throughout; do not switch to English.
- Same arithmetic discipline: every amount comes from the `authoritative` block; never recalculate.
- Keep the answer format even in Pidgin: working first, headline LAST ("... Total tax na NGN X." / "... Saving na NGN Y.").
- `required_terms` must appear (numbers and key terms can stay in their standard form).

Output: `data/sft_generated/layer_c/batch_NNN.jsonl` with the same object shape, language "pcm".
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scale", type=float, default=1.0, help="scale factor for layer sizes")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    ruleset = load_ruleset()
    calcs, counterfactuals = load_scenarios()
    rng.shuffle(calcs)
    rng.shuffle(counterfactuals)

    def n(base: int) -> int:
        return max(1, int(base * args.scale))

    layer_a = (
        build_accumulate(calcs, rng, n(80))
        + build_counterfactual(counterfactuals, rng, n(70))
        + build_correction(calcs, rng, n(40), ruleset)
        + build_clarify(calcs, rng, n(35), ruleset)
        + build_topic_shift(calcs, FACT_BLUEPRINTS, rng, n(35))
        + build_scope(calcs, rng, n(40))
    )
    layer_b = build_coaching(counterfactuals, FACT_BLUEPRINTS, rng, n(80), ruleset)
    layer_c = (
        build_accumulate(calcs, rng, n(40))
        + build_counterfactual(counterfactuals, rng, n(30))
        + build_correction(calcs, rng, n(15), ruleset)
        + build_clarify(calcs, rng, n(10), ruleset)
        + build_scope(calcs, rng, n(15))
    )
    for blueprint in layer_c:
        blueprint["language"] = "pcm"
        blueprint["conversation_id"] = blueprint["conversation_id"].replace("sft-a-", "sft-c-")

    JA = n(300)
    JB = n(80)
    JC = n(120)
    layer_a = layer_a[:JA]
    layer_b = layer_b[:JB]
    layer_c = layer_c[:JC]

    jobs_a = write_layer("layer_a", layer_a, args.batch_size, LAYER_A_INSTRUCTIONS)
    jobs_b = write_layer("layer_b", layer_b, args.batch_size, LAYER_B_INSTRUCTIONS)
    jobs_c = write_layer("layer_c", layer_c, args.batch_size, LAYER_C_INSTRUCTIONS)

    index = f"""# SFT Job Index

Generated by `scripts/build_sft_jobs.py` (seed {args.seed}, batch size {args.batch_size}).

| Layer | Conversations | Batch files | Model suggestion | Output dir |
|---|---:|---:|---|---|
| A (English bulk) | {len(layer_a)} | {jobs_a} | DeepSeek v4.1 Flash or equivalent | `data/sft_generated/layer_a/` |
| B (English coaching) | {len(layer_b)} | {jobs_b} | strongest available model | `data/sft_generated/layer_b/` |
| C (Pidgin) | {len(layer_c)} | {jobs_c} | best available + human review | `data/sft_generated/layer_c/` |

Process one layer at a time, one batch per request. After generation, run:

    uv run python scripts/verify_sft_generation.py --layer layer_a
    uv run python scripts/verify_sft_generation.py --layer layer_b
    uv run python scripts/verify_sft_generation.py --layer layer_c
"""
    (JOBS / "INDEX.md").write_text(index)
    print(f"wrote {len(layer_a)} layer_a blueprints ({jobs_a} batches)")
    print(f"wrote {len(layer_b)} layer_b blueprints ({jobs_b} batches)")
    print(f"wrote {len(layer_c)} layer_c blueprints ({jobs_c} batches)")
    print(f"jobs -> {JOBS}")


if __name__ == "__main__":
    main()
