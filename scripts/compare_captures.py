#!/usr/bin/env python3
"""Compare two stage captures side by side over the same prompt set.

Scores calculation records against engine ground truth (reusing the eval
regexes), groups paraphrase variants, handles multi-turn captures, and writes
a markdown report plus an optional JSON summary.

Usage:
    uv run python scripts/compare_captures.py \
      --before data/eval/baselines/base_qwen3_1.7b.jsonl \
      --after data/captures/sft_qwen3_1.7b.jsonl \
      --out reports/base_vs_sft.md

Ground truth is read from the capture records when present, else looked up by
id in the default eval files under data/eval/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eval_qlora import CHARGEABLE_INCOME_RE, TOTAL_TAX_RE, extract_labeled_amount  # noqa: E402

SAVINGS_RE = re.compile(
    r"(?:save|saves|saving|savings|save you)[^.\n]{0,40}?"
    r"(?:NGN|\u20a6|N(?=\d))\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

DEFAULT_PROMPT_FILES = [
    "data/eval/baseline_prompts.jsonl",
    "data/eval/probe_prompts_heldout.jsonl",
    "data/eval/final_eval_v5_unique.jsonl",
    "data/eval/paraphrase_suite.jsonl",
    "data/eval/coach_eval.jsonl",
    "data/eval/multiturn_suite.jsonl",
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_truth_lookup() -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for rel in DEFAULT_PROMPT_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        for row in load_jsonl(path):
            truth = row.get("ground_truth")
            if truth is None and "turns" not in row:
                for key in ("expected_chargeable_income", "expected_total_tax"):
                    if key in row:
                        truth = truth or {}
                        truth[key] = row[key]
            if truth:
                lookup[row["id"]] = truth
            if "turns" in row:
                for index, turn in enumerate(row["turns"]):
                    if "ground_truth" in turn:
                        lookup[f"{row['id']}#{index}"] = turn["ground_truth"]
    return lookup


def score_amount(predicted, expected):
    if predicted is None or expected is None:
        return None, None
    exact = predicted == expected
    tol = abs(float(predicted) - float(expected)) <= 1.0
    return exact, tol


def score_capture_record(record: dict, truth: dict | None) -> dict:
    """Score one (prompt, answer) pair. Returns metric dict (values may be None)."""
    answer = record.get("answer") or ""
    metrics: dict = {}
    if truth and truth.get("expected_total_tax") is not None:
        expected_tax = str(truth["expected_total_tax"])
        expected_ci = truth.get("expected_chargeable_income")
        predicted_tax = extract_labeled_amount(answer, TOTAL_TAX_RE)
        predicted_ci = extract_labeled_amount(answer, CHARGEABLE_INCOME_RE) if expected_ci else None
        metrics["expected_total_tax"] = expected_tax
        metrics["predicted_total_tax"] = predicted_tax
        exact, tol = score_amount(predicted_tax, expected_tax)
        metrics["tax_exact"] = exact
        metrics["tax_tol"] = tol
        if expected_ci:
            metrics["expected_chargeable_income"] = str(expected_ci)
            metrics["predicted_chargeable_income"] = predicted_ci
            metrics["ci_exact"] = predicted_ci == str(expected_ci)
        if truth.get("expected_savings") is not None:
            expected_savings = str(truth["expected_savings"])
            predicted_savings = extract_labeled_amount(answer, SAVINGS_RE)
            metrics["expected_savings"] = expected_savings
            metrics["predicted_savings"] = predicted_savings
            exact, tol = score_amount(predicted_savings, expected_savings)
            metrics["savings_exact"] = exact
            metrics["savings_tol"] = tol
    return metrics


def flatten_single(records: list[dict]) -> list[dict]:
    out = []
    for record in records:
        out.append(
            {
                "id": record["id"],
                "language": record.get("language", "en"),
                "category": record.get("category", "unknown"),
                "prompt": record.get("prompt") or record.get("instruction", ""),
                "answer": record.get("answer", ""),
            }
        )
    return out


def flatten_multiturn(records: list[dict]) -> list[dict]:
    out = []
    for record in records:
        for index, turn in enumerate(record.get("turns", [])):
            out.append(
                {
                    "id": f"{record['id']}#{index}",
                    "group": record["id"],
                    "language": record.get("language", "en"),
                    "category": record.get("category", "multi_turn"),
                    "prompt": turn["user"],
                    "answer": turn.get("answer", ""),
                    "ground_truth": turn.get("ground_truth"),
                }
            )
    return out


def flatten(records: list[dict]) -> list[dict]:
    if records and "turns" in records[0]:
        return flatten_multiturn(records)
    return flatten_single(records)


def summarize(rows: list[dict], truth_lookup: dict[str, dict]) -> dict:
    stats = {
        "records": len(rows),
        "calc": 0, "tax_exact": 0, "tax_tol": 0,
        "ci": 0, "ci_exact": 0,
        "savings": 0, "savings_exact": 0, "savings_tol": 0,
    }
    for row in rows:
        truth = row.get("ground_truth") or truth_lookup.get(row["id"])
        row["metrics"] = score_capture_record(row, truth)
        metrics = row["metrics"]
        if "tax_exact" in metrics:
            stats["calc"] += 1
            stats["tax_exact"] += bool(metrics["tax_exact"])
            stats["tax_tol"] += bool(metrics["tax_tol"])
        if "ci_exact" in metrics:
            stats["ci"] += 1
            stats["ci_exact"] += bool(metrics["ci_exact"])
        if "savings_exact" in metrics:
            stats["savings"] += 1
            stats["savings_exact"] += bool(metrics["savings_exact"])
            stats["savings_tol"] += bool(metrics["savings_tol"])
    return stats


def pct(part: int, whole: int) -> str:
    return f"{part}/{whole} = {100 * part / whole:.0f}%" if whole else "n/a"


def paraphrase_consistency(rows: list[dict]) -> tuple[int, int, list[str]]:
    """A group is consistent when all variants with predictions give the same
    predicted annual tax (across all phrasings of the same core)."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        group = row["id"].rsplit("-", 1)[0]
        if group.startswith("para-"):
            groups.setdefault(group, []).append(row)
    consistent = 0
    total = 0
    inconsistent = []
    for group, members in sorted(groups.items()):
        predictions = {
            m["metrics"].get("predicted_total_tax")
            for m in members
            if m["metrics"].get("predicted_total_tax") is not None
        }
        if not predictions:
            continue  # fact group or no parseable answers
        total += 1
        if len(predictions) == 1:
            consistent += 1
        else:
            inconsistent.append(f"{group}: {sorted(predictions)}")
    return consistent, total, inconsistent


def write_report(
    before_path: Path, after_path: Path,
    before_rows: list[dict], after_rows: list[dict],
    before_stats: dict, after_stats: dict, out_path: Path,
) -> None:
    lines: list[str] = []
    lines.append("# Stage Comparison Report")
    lines.append("")
    lines.append(f"- **before:** `{before_path}` ({before_stats['records']} records)")
    lines.append(f"- **after:** `{after_path}` ({after_stats['records']} records)")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Before | After |")
    lines.append("|---|---|---|")
    rows = [
        ("calculations scored", "calc"),
        ("tax exact", "tax_exact"),
        ("tax within NGN 1", "tax_tol"),
        ("chargeable income exact", "ci_exact"),
        ("chargeable income scored", "ci"),
        ("savings exact", "savings_exact"),
        ("savings scored", "savings"),
    ]
    for label, key in rows:
        lines.append(f"| {label} | {before_stats[key]} | {after_stats[key]} |")
    lines.append("")
    lines.append("| Rate | Before | After |")
    lines.append("|---|---|---|")
    lines.append(f"| tax exact | {pct(before_stats['tax_exact'], before_stats['calc'])} | {pct(after_stats['tax_exact'], after_stats['calc'])} |")
    lines.append(f"| tax within NGN 1 | {pct(before_stats['tax_tol'], before_stats['calc'])} | {pct(after_stats['tax_tol'], after_stats['calc'])} |")
    lines.append(f"| chargeable income | {pct(before_stats['ci_exact'], before_stats['ci'])} | {pct(after_stats['ci_exact'], after_stats['ci'])} |")
    lines.append(f"| savings exact | {pct(before_stats['savings_exact'], before_stats['savings'])} | {pct(after_stats['savings_exact'], after_stats['savings'])} |")
    lines.append("")

    b_cons = paraphrase_consistency(before_rows)
    a_cons = paraphrase_consistency(after_rows)
    lines.append("## Paraphrase consistency (same predicted tax across 5 phrasings)")
    lines.append("")
    lines.append(f"- before: {b_cons[0]}/{b_cons[1]} groups consistent")
    lines.append(f"- after: {a_cons[0]}/{a_cons[1]} groups consistent")
    if b_cons[2]:
        lines.append("")
        lines.append("Before inconsistencies: " + "; ".join(b_cons[2]))
    if a_cons[2]:
        lines.append("")
        lines.append("After inconsistencies: " + "; ".join(a_cons[2]))
    lines.append("")

    before_by_id = {row["id"]: row for row in before_rows}
    after_by_id = {row["id"]: row for row in after_rows}
    common = sorted(set(before_by_id) & set(after_by_id))

    improved, regressed = [], []
    for pid in common:
        b = before_by_id[pid]["metrics"].get("tax_exact")
        a = after_by_id[pid]["metrics"].get("tax_exact")
        if b is None or a is None:
            continue
        if a and not b:
            improved.append(pid)
        if b and not a:
            regressed.append(pid)

    lines.append("## Movement")
    lines.append("")
    lines.append(f"- improved (tax wrong -> right): {len(improved)}")
    lines.append(f"- regressed (tax right -> wrong): {len(regressed)}")
    if improved:
        lines.append(f"  - improved: {', '.join(improved)}")
    if regressed:
        lines.append(f"  - regressed: {', '.join(regressed)}")
    lines.append("")

    lines.append("## Per-prompt detail")
    lines.append("")
    for pid in common:
        b = before_by_id[pid]
        a = after_by_id[pid]
        lines.append(f"### {pid}")
        lines.append("")
        lines.append(f"**Prompt:** {b['prompt'][:300]}")
        if b["metrics"].get("expected_total_tax") is not None:
            lines.append(f"**Expected tax:** {b['metrics'].get('expected_total_tax')} | "
                         f"before: {b['metrics'].get('predicted_total_tax')} | after: {a['metrics'].get('predicted_total_tax')}")
        lines.append("")
        lines.append(f"**Before:** {b['answer'][:600].replace(chr(10), ' ')}")
        lines.append("")
        lines.append(f"**After:** {a['answer'][:600].replace(chr(10), ' ')}")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="markdown report path")
    parser.add_argument("--json", type=Path, help="optional JSON summary path")
    args = parser.parse_args()

    truth_lookup = load_truth_lookup()
    before_rows = flatten(load_jsonl(args.before))
    after_rows = flatten(load_jsonl(args.after))
    before_stats = summarize(before_rows, truth_lookup)
    after_stats = summarize(after_rows, truth_lookup)

    write_report(args.before, args.after, before_rows, after_rows, before_stats, after_stats, args.out)
    print(f"wrote report -> {args.out}")
    print(
        f"tax exact before/after: {before_stats['tax_exact']}/{before_stats['calc']} -> "
        f"{after_stats['tax_exact']}/{after_stats['calc']}"
    )

    if args.json:
        summary = {
            "before": str(args.before),
            "after": str(args.after),
            "before_stats": before_stats,
            "after_stats": after_stats,
        }
        args.json.write_text(json.dumps(summary, indent=2))
        print(f"wrote json   -> {args.json}")


if __name__ == "__main__":
    main()
