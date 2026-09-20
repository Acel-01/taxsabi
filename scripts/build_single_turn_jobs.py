#!/usr/bin/env python3
"""Build single-turn Q&A jobs (Layer 2), batched like the conversation jobs.

Each record is a 2-turn conversation (user question + assistant answer) so the
same verifier and training renderer handle it unchanged. Three phrasing
variants per calculation/counterfactual scenario, plus direct fact Q&A.

Layers:
  single_en    English single-turn   (~1,100)
  single_pcm   Pidgin single-turn    (~150)

Usage:
    uv run python scripts/build_single_turn_jobs.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset  # noqa: E402

SCENARIOS = ROOT / "data" / "scenarios"
JOBS = ROOT / "data" / "sft_jobs"

# 12 facts x 8 question styles
FACTS = [
    {
        "id": "bands",
        "subject": "the 2026 personal income tax bands and rates",
        "required_terms": ["800,000", "0%", "15%", "18%", "21%", "23%", "25%"],
        "source_fact_ids": ["F-001"],
    },
    {
        "id": "rent",
        "subject": "the rent relief rule, including the cap",
        "required_terms": ["20%", "500,000"],
        "source_fact_ids": ["F-004"],
    },
    {
        "id": "minwage",
        "subject": "the minimum wage exemption",
        "required_terms": ["70,000", "exempt"],
        "source_fact_ids": ["F-009", "F-015"],
    },
    {
        "id": "paye",
        "subject": "when PAYE must be remitted and the employer annual return deadline",
        "required_terms": ["10th", "31 January"],
        "source_fact_ids": ["F-011"],
    },
    {
        "id": "pension",
        "subject": "the mandatory pension contribution rates",
        "required_terms": ["10%", "8%"],
        "source_fact_ids": ["F-014"],
    },
    {
        "id": "vpc",
        "subject": "the voluntary pension contribution limits and channel",
        "required_terms": ["one-third", "writing", "employer"],
        "source_fact_ids": ["F-014"],
    },
    {
        "id": "filing",
        "subject": "where and how relief claims are filed",
        "required_terms": ["annual return", "written"],
        "source_fact_ids": ["F-017"],
    },
    {
        "id": "refund",
        "subject": "how overpaid tax is refunded and the timelines",
        "required_terms": ["90 days", "six years"],
        "source_fact_ids": ["F-018"],
    },
    {
        "id": "evidence",
        "subject": "what proof a deduction claim needs",
        "required_terms": ["writing", "documentary evidence"],
        "source_fact_ids": ["F-005", "F-012"],
    },
    {
        "id": "nocra",
        "subject": "whether the consolidated relief allowance still exists",
        "required_terms": ["consolidated relief allowance"],
        "source_fact_ids": ["F-010"],
    },
    {
        "id": "objection",
        "subject": "how to dispute an assessment",
        "required_terms": ["30 days", "written"],
        "source_fact_ids": ["F-019"],
    },
    {
        "id": "scope",
        "subject": "whether company tax and VAT are covered",
        "required_terms": ["personal income tax"],
        "source_fact_ids": ["F-008"],
    },
]

CITATIONS = {
    "bands": "Fourth Schedule (section 58) of the Nigeria Tax Act 2025",
    "rent": "section 30(2)(a)(vi) of the Nigeria Tax Act 2025",
    "minwage": "section 58 of the Nigeria Tax Act 2025",
    "paye": "section 51 of the Nigeria Tax Administration Act 2025",
    "pension": "section 30(2)(a)(iii) of the Nigeria Tax Act 2025",
    "vpc": "section 30(2)(a)(iii) of the Nigeria Tax Act 2025",
    "filing": "section 30(2)(a) of the Nigeria Tax Act 2025",
    "refund": "section 55 of the Nigeria Tax Administration Act 2025",
    "evidence": "sections 31 and 32 of the Nigeria Tax Act 2025",
    "nocra": "section 30 of the Nigeria Tax Act 2025",
    "objection": "section 41 of the Nigeria Tax Administration Act 2025",
    "scope": "the Nigeria Tax Act 2025",
}

CITED_STYLES = [
    ("cited_formal", "ask formally and require the answer to cite the exact legal provision"),
    ("cited_conversational", "ask naturally and require the citation to be woven into the answer"),
    ("cited_direct", "ask directly and require the exact section cited in the answer"),
]

CITED_STYLES_PIDGIN = [
    ("cited_pidgin_formal", "ask in Pidgin formally and require the answer to cite the exact legal provision"),
    ("cited_pidgin_conversational", "ask in natural Pidgin and require the citation woven into the answer"),
]

# 8 question styles for regular facts
QUESTION_STYLES = [
    ("direct", "ask the question directly and plainly"),
    ("terse", "ask in a few words, shorthand style"),
    ("verify", "say someone told them something about this and ask if it is correct"),
    ("context", "give a one-line personal context first, then ask"),
    ("explain", "ask for a simple explanation"),
    ("list", "ask for the full list or the exact figures"),
    ("command", "phrase it as a short command, e.g. 'break this down for me'"),
    ("confused", "say they are confused about this and need it cleared up"),
]

QUESTION_STYLES = [
    ("direct", "ask the question directly and plainly"),
    ("terse", "ask in a few words, shorthand style"),
    ("verify", "say someone told them something about this and ask if it is correct"),
    ("context", "give a one-line personal context first, then ask"),
    ("explain", "ask for a simple explanation"),
    ("list", "ask for the full list or the exact figures"),
    ("command", "phrase it as a short command, e.g. 'break this down for me'"),
    ("confused", "say they are confused about this and need it cleared up"),
]

CALC_STYLES = [
    ("standard", "ask directly, stating all the facts in one natural sentence"),
    ("shorthand", "use shorthand amounts like 3.6m and 800k where exact"),
    ("context", "give a brief context (planning, filing, checking a payslip) before asking"),
]

CF_STYLES = [
    ("standard", "state the facts, ask the tax, then ask the what-if in the same question"),
    ("shorthand", "use shorthand amounts; ask what the change would save"),
    ("verify", "say an adviser claimed the change saves a certain amount and ask them to check it"),
]


def gt_block(gt: dict) -> dict:
    return {
        "gross_annual_salary": gt["gross_annual_salary"],
        "relief_inputs": gt.get("relief_inputs", {}),
        "applied_reliefs": gt.get("applied_reliefs", {}),
        "total_relief": gt.get("total_relief", "0.00"),
        "chargeable_income": gt["expected_chargeable_income"],
        "total_tax": gt["expected_total_tax"],
        "tax_breakdown": gt.get("tax_breakdown", []),
    }


def build_calc(scenarios: list[dict], language: str, offset: int, count: int, variant: int = 0) -> list[dict]:
    out = []
    for i in range(count):
        scenario = scenarios[i % len(scenarios)]
        gt = gt_block(scenario["ground_truth"])
        style = CALC_STYLES[(i + variant) % len(CALC_STYLES)]
        pid = f"st-{'en' if language == 'en' else 'pcm'}-calc-{offset + i:04d}"
        out.append(
            {
                "conversation_id": pid,
                "type": "single_calc",
                "language": language,
                "style": style[0],
                "turns": [{"role": "user", "guidance": f"{style[1]}; the assistant answers with the tax"}],
                "authoritative": gt,
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return out


def build_cf(scenarios: list[dict], language: str, offset: int, count: int, variant: int = 0) -> list[dict]:
    out = []
    for i in range(count):
        scenario = scenarios[i % len(scenarios)]
        gt = scenario["ground_truth"]
        field = gt["changed_field"]
        new_value = gt.get(f"new_{field}") or gt.get("new_value")
        base_reliefs = {k: float(v) for k, v in gt.get("base_relief_inputs", {}).items()}
        if field in base_reliefs:
            change = f"increasing their {field} to {new_value} (currently {format(base_reliefs[field], '.2f')})"
            extra = round(float(new_value) - base_reliefs[field], 2)
        else:
            change = f"adding {new_value} of {field}"
            extra = float(new_value)
        style = CF_STYLES[(i + variant) % len(CF_STYLES)]
        pid = f"st-{'en' if language == 'en' else 'pcm'}-cf-{offset + i:04d}"
        out.append(
            {
                "conversation_id": pid,
                "type": "single_counterfactual",
                "language": language,
                "style": style[0],
                "turns": [
                    {
                        "role": "user",
                        "guidance": (
                            f"state salary and every base payment ({gt.get('base_relief_inputs', {})}), "
                            f"ask the tax and what it becomes when {change}; {style[1]}. "
                            "The assistant leads with the saving."
                        ),
                    }
                ],
                "authoritative": {
                    "gross_annual_salary": gt["gross_annual_salary"],
                    "base_relief_inputs": gt.get("base_relief_inputs", {}),
                    "base_chargeable_income": gt["base_chargeable_income"],
                    "base_tax": gt["base_tax"],
                    "changed_field": field,
                    "new_value": format(float(new_value), ".2f"),
                    "extra_amount": format(extra, ".2f"),
                    "scenario_chargeable_income": gt["scenario_chargeable_income"],
                    "scenario_tax": gt["scenario_tax"],
                    "tax_saving": gt["tax_saving"],
                },
                "source_fact_ids": scenario.get("source_fact_ids", []),
                "scenario_id": scenario["scenario_id"],
                "scenario_family": scenario.get("scenario_family"),
            }
        )
    return out


def build_facts(facts: list[dict], language: str, variants_per_fact: int) -> list[dict]:
    out = []
    for fact in facts:
        # Regular variants
        for j, style in enumerate(QUESTION_STYLES[:variants_per_fact]):
            pid = f"st-{'en' if language == 'en' else 'pcm'}-fact-{fact['id']}-{j:02d}"
            out.append(
                {
                    "conversation_id": pid,
                    "type": "single_fact",
                    "language": language,
                    "style": style[0],
                    "turns": [
                        {
                            "role": "user",
                            "guidance": f"{style[1]}; the question is about {fact['subject']}",
                        }
                    ],
                    "authoritative": {},
                    "required_terms": fact["required_terms"],
                    "source_fact_ids": fact["source_fact_ids"],
                }
            )
        # Cited variants: 2 per fact (formal + conversational citation)
        cited_styles = CITED_STYLES if language == "en" else CITED_STYLES_PIDGIN
        for j, style in enumerate(cited_styles[:2]):
            pid = f"st-{'en' if language == 'en' else 'pcm'}-fact-cited-{fact['id']}-{j:02d}"
            citation = CITATIONS[fact["id"]]
            out.append(
                {
                    "conversation_id": pid,
                    "type": "single_fact_cited",
                    "language": language,
                    "style": style[0],
                    "turns": [
                        {
                            "role": "user",
                            "guidance": f"{style[1]}; the question is about {fact['subject']}; the answer must cite the exact legal provision",
                        }
                    ],
                    "authoritative": {"citation": CITATIONS[fact["id"]]},
                    "required_terms": fact["required_terms"] + [CITATIONS[fact["id"]]],
                    "source_fact_ids": fact["source_fact_ids"],
                }
            )
    return out


INSTRUCTIONS = """# Single-turn {label}

Every blueprint is a 2-turn conversation: one user question, one assistant answer. Follow `{ref}` tone rules. Write only the user question (per its `guidance` and `style`) and the assistant answer.

Answer format:
- Calculation/single_calc: "Total tax: NGN X. Gross income: NGN G. Reliefs applied: ... total relief NGN R. Chargeable income: NGN C. Band breakdown: ..."
- Counterfactual/single_counterfactual: "Saving: NGN S. Your tax drops from NGN A to NGN B. [one-line reason]"
- Fact/single_fact: concise prose; every `required_terms` item must appear verbatim (case-insensitive); no invented figures.

Number discipline: use ONLY values from the blueprint `authoritative` block; never invent, recalculate, or round. Amount format "NGN 3,000,000" (comma separators, no .00).

Method: temporary Python script via heredoc defining the question and answer per conversation_id, then merging blueprint fields (id from conversation_id, type, language, authoritative, required_terms, source_fact_ids, scenario_id, scenario_family) plus generated_by "opencode".

Do not modify other files. Do not run scripts/verify_sft_generation.py. Return one line per batch handled.
"""


def write_layer(layer: str, items: list[dict], batch_size: int, label: str, ref: str) -> int:
    layer_dir = JOBS / layer
    if layer_dir.exists():
        shutil.rmtree(layer_dir)
    layer_dir.mkdir(parents=True)
    (layer_dir / "README.md").write_text(INSTRUCTIONS.format(label=label, ref=ref))
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
    for n, batch in enumerate(batches, 1):
        with open(layer_dir / f"batch_{n:03d}.jsonl", "w") as fh:
            for item in batch:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return len(batches)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()

    calcs = [json.loads(line) for line in (SCENARIOS / "train.jsonl").read_text().splitlines() if line.strip()]
    cfs = [json.loads(line) for line in (SCENARIOS / "counterfactual_train.jsonl").read_text().splitlines() if line.strip()]

    # English: 3 variants per scenario (each scenario gets all three styles)
    en_calc = (
        build_calc(calcs, "en", 0, len(calcs), 0)
        + build_calc(calcs, "en", 1000, len(calcs), 1)
        + build_calc(calcs, "en", 2000, len(calcs), 2)
    )
    en_cf = (
        build_cf(cfs, "en", 0, len(cfs), 0)
        + build_cf(cfs, "en", 1000, len(cfs), 1)
        + build_cf(cfs, "en", 2000, len(cfs), 2)
    )
    en_facts = build_facts(FACTS, "en", 8)
    en = en_calc + en_cf + en_facts

    # Pidgin: ~100 calc/cf variants + 50 fact variants
    pcm_calc = (
        build_calc(calcs[:20], "pcm", 0, 20, 0)
        + build_calc(calcs[:20], "pcm", 1000, 20, 1)
        + build_calc(calcs[:20], "pcm", 2000, 20, 2)
    )
    pcm_cf = build_cf(cfs[:12], "pcm", 0, 12, 0) + build_cf(cfs[:12], "pcm", 1000, 12, 1)
    pcm_facts = build_facts(FACTS[:10], "pcm", 5)
    pcm = pcm_calc + pcm_cf + pcm_facts

    batches_en = write_layer("single_en", en, args.batch_size, "English Q&A", "data/sft_jobs/layer_a/README.md")
    batches_pcm = write_layer("single_pcm", pcm, args.batch_size, "Pidgin Q&A", "data/sft_jobs/layer_c/README.md")

    print(f"single_en: {len(en)} items in {batches_en} batches")
    print(f"single_pcm: {len(pcm)} items in {batches_pcm} batches")


if __name__ == "__main__":
    main()
