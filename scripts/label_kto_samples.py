#!/usr/bin/env python3
"""Label KTO samples deterministically and assemble the KTO dataset (Phase 3.1).

Labels come from the `labeler` rule named in each prompt record; no model judge
is used in v1 (the plan's LLM-judge labels are a later pass):

    engine_tax          final total tax exactly matches the rules engine
    engine_saving       stated saving (or from/to tax pair) matches the engine
    fact_terms          all required terms present, no unauthorised amounts,
                        no invented section or act year
    fact_terms_cited    as fact_terms plus the expected citation present
    clarify_no_compute  asks monthly vs annual and states no tax figure

Verified gold completions are always labelled desirable (any gold that fails a
labeler rule is counted and reported - it means a rule needs fixing).

Output: `data/kto/{train,val}.jsonl` (KTO: prompt/completion message lists +
bool label), `data/kto/label_stats.json`, `data/kto/MANIFEST.md`.

Usage:
    uv run python scripts/label_kto_samples.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_captures import SAVINGS_RE  # noqa: E402
from eval_qlora import CHARGEABLE_INCOME_RE, TOTAL_TAX_RE, norm_amount  # noqa: E402
from verify_sft_generation import (  # noqa: E402
    BAND_NUMBER_RE,
    CONSTANTS,
    amount_in_set,
    collect_values,
    extract_amounts,
    parse_decimal,
)

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)

FROM_TO_RE = re.compile(
    r"from\s+(?:NGN\s*)?([\d,]+(?:\.\d{1,2})?)\s+to\s+(?:NGN\s*)?([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"section\s+(\d+)", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
BASE_SECTIONS = {"4", "30", "31", "32", "41", "51", "55", "58"}
ALLOWED_YEARS = {"2014", "2024", "2025", "2026"}


def load_allowed_sections() -> set[str]:
    """Every section reference traced in the source register may be cited."""
    sections = set(BASE_SECTIONS)
    register = ROOT / "sources" / "SOURCE_REGISTER.md"
    if register.exists():
        text = register.read_text()
        sections.update(re.findall(r"\bs\.\s*(\d+)", text))
        sections.update(re.findall(r"\bsection\s+(\d+)", text, re.IGNORECASE))
    return sections


ALLOWED_SECTIONS = load_allowed_sections()
MONTHLY_MARKERS = ("monthly", "every month", "per month", "a month", "month by month")
ANNUAL_MARKERS = ("annual", "annually", "yearly", "every year", "per year", "a year")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fact_allowed(item: dict) -> set:
    values = set(CONSTANTS)
    collect_values(item.get("authoritative", {}), values)
    for term in item.get("required_terms", []):
        for number in BAND_NUMBER_RE.findall(term):
            parsed = parse_decimal(number)
            if parsed is not None:
                values.add(parsed)
    return values


def citation_problems(item: dict, text: str) -> list[str]:
    problems = []
    expected = item.get("expected_citation") or ""
    allowed_sections = set(ALLOWED_SECTIONS)
    allowed_sections.update(SECTION_RE.findall(expected))
    found = set(SECTION_RE.findall(text))
    invented = found - allowed_sections
    if invented:
        problems.append("invented section: " + ", ".join(sorted(invented)))
    term_years = {year for term in item.get("required_terms", [])
                  for year in YEAR_RE.findall(term)}
    years = set(YEAR_RE.findall(text)) - ALLOWED_YEARS - term_years
    if years and re.search(r"\b(act|law|decree|section)\b", text, re.IGNORECASE):
        problems.append("invented act year: " + ", ".join(sorted(years)))
    return problems


def label_calc(item: dict, text: str) -> tuple[bool, str, str | None, str | None]:
    expected = norm_amount(str(item["authoritative"]["total_tax"]))
    predicted = None
    match = list(TOTAL_TAX_RE.finditer(text))
    if match:
        predicted = norm_amount(match[-1].group(1))
    if predicted is None:
        return False, "no_total_stated", None, expected
    if predicted == expected:
        return True, "total_exact", predicted, expected
    return False, "total_mismatch", predicted, expected


def label_counterfactual(item: dict, text: str) -> tuple[bool, str, str | None, str | None]:
    auth = item["authoritative"]
    expected_saving = norm_amount(str(auth["tax_saving"]))
    expected_pair = f"{norm_amount(str(auth['base_tax']))} -> {norm_amount(str(auth['scenario_tax']))}"
    matches = list(SAVINGS_RE.finditer(text))
    if matches:
        saving = norm_amount(matches[-1].group(1))
        if saving == expected_saving:
            return True, "saving_exact", saving, expected_saving
        return False, "saving_mismatch", saving, expected_saving
    pair = FROM_TO_RE.search(text)
    if pair:
        stated = f"{norm_amount(pair.group(1))} -> {norm_amount(pair.group(2))}"
        if stated == expected_pair:
            return True, "from_to_exact", stated, expected_pair
        return False, "from_to_mismatch", stated, expected_pair
    return False, "no_saving_stated", None, expected_saving


def label_fact(item: dict, text: str) -> tuple[bool, str, str | None, str | None]:
    missing = [term for term in item.get("required_terms", [])
               if term.lower() not in text.lower()]
    if missing:
        return False, "missing_terms: " + ", ".join(missing[:3]), None, None
    allowed = fact_allowed(item)
    bad = [amount for amount in extract_amounts(text) if not amount_in_set(amount, allowed)]
    if bad:
        return False, "unauthorised_amounts: " + ", ".join(str(v) for v in sorted(bad)[:3]), None, None
    problems = citation_problems(item, text)
    if problems:
        return False, "; ".join(problems), None, None
    return True, "terms_and_citation_clean", None, None


def label_clarify(item: dict, text: str) -> tuple[bool, str, str | None, str | None]:
    low = text.lower()
    monthly = any(marker in low for marker in MONTHLY_MARKERS)
    annual = any(marker in low for marker in ANNUAL_MARKERS)
    if list(TOTAL_TAX_RE.finditer(text)):
        return False, "computed_instead_of_asking", None, None
    if monthly and annual:
        return True, "asks_period", None, None
    return False, "no_period_question", None, None


LABELERS = {
    "engine_tax": label_calc,
    "engine_saving": label_counterfactual,
    "fact_terms": label_fact,
    "fact_terms_cited": label_fact,
    "clarify_no_compute": label_clarify,
}


def label_item(item: dict, text: str) -> tuple[bool, str, str | None, str | None]:
    labeler = LABELERS[item["labeler"]]
    return labeler(item, text)


def make_row(item: dict, text: str, source: str, sample_index: int | None,
             label: bool, reason: str, predicted=None, expected=None) -> dict:
    suffix = "gold" if source == "gold" else f"s{sample_index}"
    row = {
        "id": f"{item['id']}::{suffix}",
        "prompt_id": item["id"],
        "prompt": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["prompt"]},
        ],
        "completion": [{"role": "assistant", "content": text}],
        "label": label,
        "type": item["type"],
        "language": item["language"],
        "source": source,
        "reason": reason,
        "prompt_text": item["prompt"],
        "completion_text": text,
    }
    if predicted is not None:
        row["predicted"] = predicted
    if expected is not None:
        row["expected"] = expected
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", type=Path, default=ROOT / "data" / "kto" / "prompts.jsonl")
    parser.add_argument("--samples", type=Path, default=ROOT / "data" / "kto" / "samples.jsonl")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "kto")
    args = parser.parse_args()

    prompts = load_jsonl(args.prompts)
    prompt_by_id = {item["id"]: item for item in prompts}
    if not args.samples.exists():
        raise SystemExit(f"samples not found: {args.samples} (run the sampler on the instance first)")
    samples = load_jsonl(args.samples)

    by_prompt: dict[str, list[tuple[int, str]]] = defaultdict(list)
    unknown = 0
    seen: set[tuple[str, int]] = set()
    for row in samples:
        pid = row["id"]
        key = (pid, row["sample"])
        if key in seen:
            continue
        seen.add(key)
        if pid not in prompt_by_id:
            unknown += 1
            continue
        by_prompt[pid].append((row["sample"], row["answer"]))
    if unknown:
        raise SystemExit(f"FAIL: {unknown} samples reference unknown prompt ids")

    rows: list[dict] = []
    stats = Counter()
    reasons = Counter()
    gold_failures: list[str] = []
    prompt_stats: list[dict] = []

    for item in prompts:
        desired = 0
        sampled = 0
        if item.get("gold_completion"):
            label, reason, predicted, expected = label_item(item, item["gold_completion"])
            if not label:
                gold_failures.append(f"{item['id']}: {reason}")
            rows.append(make_row(item, item["gold_completion"], "gold", None, True,
                                 "gold_verified" if label else f"gold_verified ({reason})",
                                 predicted, expected))
            stats["gold"] += 1
        for index, answer in sorted(by_prompt.get(item["id"], [])):
            label, reason, predicted, expected = label_item(item, answer)
            rows.append(make_row(item, answer, "sample", index, label, reason,
                                 predicted, expected))
            stats["desirable" if label else "undesirable"] += 1
            stats[f"sample_{item['type']}"] += 1
            reasons[reason.split(":")[0]] += 1
            sampled += 1
            desired += int(label)
        if sampled:
            prompt_stats.append({
                "prompt_id": item["id"],
                "type": item["type"],
                "language": item["language"],
                "source": item["source"],
                "samples": sampled,
                "desirable": desired,
            })

    train = [row for row in rows if prompt_by_id[row["prompt_id"]]["split"] == "train"]
    val = [row for row in rows if prompt_by_id[row["prompt_id"]]["split"] == "val"]

    train_desirable = sum(1 for row in train if row["label"])
    if not train_desirable or train_desirable == len(train):
        print("WARNING: one class missing in train - KTO needs both desirable and undesirable")

    args.out.mkdir(parents=True, exist_ok=True)
    for name, split_rows in (("train", train), ("val", val)):
        with open(args.out / f"{name}.jsonl", "w") as fh:
            for row in split_rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    sampled_prompts = len(prompt_stats)
    sample_total = stats["desirable"] + stats["undesirable"]
    desirable = stats["desirable"]
    by_type = defaultdict(lambda: {"samples": 0, "desirable": 0})
    for entry in prompt_stats:
        by_type[entry["type"]]["samples"] += entry["samples"]
        by_type[entry["type"]]["desirable"] += entry["desirable"]

    label_stats = {
        "prompts": len(prompts),
        "prompts_with_samples": sampled_prompts,
        "gold_examples": stats["gold"],
        "sample_examples": sample_total,
        "sample_desirable": desirable,
        "sample_undesirable": stats["undesirable"],
        "sample_desirable_rate": round(desirable / sample_total, 4) if sample_total else None,
        "by_type": {k: dict(v) for k, v in sorted(by_type.items())},
        "reasons": dict(reasons.most_common()),
        "gold_check_failures": gold_failures,
        "prompt_stats": prompt_stats,
    }
    (args.out / "label_stats.json").write_text(json.dumps(label_stats, indent=2))

    run_meta = {}
    run_meta_path = args.out / "sample_run.json"
    if run_meta_path.exists():
        run_meta = json.loads(run_meta_path.read_text())

    lines = [
        "# KTO Dataset v1 — Manifest",
        "",
        f"- Assembled: {date.today().isoformat()} from `{display(args.prompts)}` + `{display(args.samples)}`",
        f"- On-policy samples: model `{run_meta.get('model', 'unknown')}`"
        f" | temperature {run_meta.get('temperature', '?')} | {run_meta.get('samples_per_prompt', '?')} per prompt",
        f"- Total examples: {len(rows)} (train {len(train)} / val {len(val)})",
        f"- Gold (verified) examples: {stats['gold']} | on-policy samples: {sample_total}",
        f"- On-policy desirable rate: {desirable}/{sample_total} = "
        f"{(100 * desirable / sample_total):.0f}%" if sample_total else "- On-policy desirable rate: n/a",
        f"- Gold labeler check failures: {len(gold_failures)}",
        "",
        "| Type | Samples | Desirable | Rate |",
        "|---|---:|---:|---:|",
    ]
    for type_name, entry in sorted(by_type.items()):
        rate = f"{100 * entry['desirable'] / entry['samples']:.0f}%" if entry["samples"] else "n/a"
        lines.append(f"| {type_name} | {entry['samples']} | {entry['desirable']} | {rate} |")
    lines += [
        "",
        "| Split | Total | Desirable | Undesirable |",
        "|---|---:|---:|---:|",
        f"| train | {len(train)} | {train_desirable} | {len(train) - train_desirable} |",
        f"| val | {len(val)} | {sum(1 for row in val if row['label'])} | "
        f"{sum(1 for row in val if not row['label'])} |",
        "",
        "Top label reasons: " + ", ".join(f"{reason} ({count})" for reason, count in reasons.most_common(8)),
        "",
        f"Input sha256: prompts {sha256(args.prompts)} | samples {sha256(args.samples)}",
        "",
        "Label protocol: deterministic rules only (engine totals, engine savings,",
        "required terms, citation register). Verified gold answers always desirable.",
    ]
    (args.out / "MANIFEST.md").write_text("\n".join(lines) + "\n")

    print(f"prompts: {len(prompts)} | sampled: {sampled_prompts} | gold: {stats['gold']}")
    print(f"on-policy samples: {sample_total} (desirable {desirable}, undesirable {stats['undesirable']}, "
          f"rate {label_stats['sample_desirable_rate']})")
    print(f"by type: {dict(by_type)}")
    print(f"top reasons: {reasons.most_common(6)}")
    if gold_failures:
        print(f"GOLD CHECK FAILURES ({len(gold_failures)}):")
        for failure in gold_failures[:10]:
            print(f"  {failure}")
    print(f"wrote train={len(train)} val={len(val)} -> {args.out}")


if __name__ == "__main__":
    main()
