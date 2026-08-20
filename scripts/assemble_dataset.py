#!/usr/bin/env python3
"""Assemble deduplicated training records from verified JSONL sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        default=[
            ROOT / "data/train/final_english_v2.jsonl",
            ROOT / "data/train/behavior_en.jsonl",
            ROOT / "data/train/counterfactual.jsonl",
        ],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/train/final_english_v3.jsonl",
    )
    parser.add_argument("--include-unreviewed-languages", action="store_true")
    parser.add_argument("--max-calculation", type=int, default=1000)
    return parser.parse_args()


def sample_calculations(records: list[dict], maximum: int | None) -> list[dict]:
    if maximum is None:
        return records
    calculations = [
        record
        for record in records
        if record["category"] == "calculation" and record["language"] == "en"
    ]
    if len(calculations) <= maximum:
        return records

    mandatory = []
    mandatory_ids = set()
    for record in calculations:
        if record.get("scenario_family") == "shorthand_money":
            mandatory.append(record)
            mandatory_ids.add(record["id"])
    seen_scenarios = {record.get("scenario_id") for record in mandatory}
    for record in calculations:
        scenario_id = record.get("scenario_id")
        if scenario_id and scenario_id not in seen_scenarios and record["id"] not in mandatory_ids:
            mandatory.append(record)
            seen_scenarios.add(scenario_id)
    if len(mandatory) > maximum:
        raise SystemExit("--max-calculation is smaller than the number of scenarios")

    selected_ids = {record["id"] for record in mandatory}
    remaining = [record for record in calculations if record["id"] not in selected_ids]
    remaining.sort(key=lambda record: hashlib.sha256(record["id"].encode()).hexdigest())
    selected = mandatory + remaining[: maximum - len(mandatory)]
    selected_ids = {record["id"] for record in selected}

    output = []
    for record in records:
        if record["category"] != "calculation" or record["id"] in selected_ids:
            output.append(record)
    return output


def main() -> None:
    args = parse_args()
    records = []
    seen_ids = set()
    for path in args.inputs:
        for record in read_jsonl(path):
            if record["id"] in seen_ids:
                raise SystemExit(f"duplicate record id: {record['id']}")
            if record["language"] != "en" and not (
                args.include_unreviewed_languages or record["human_reviewed"]
            ):
                raise SystemExit(
                    f"refusing unreviewed non-English record: {record['id']}"
                )
            seen_ids.add(record["id"])
            records.append(record)
    records = sample_calculations(records, args.max_calculation)
    write_jsonl(args.output, records)
    print(f"wrote {len(records)} unique records to {args.output}")


if __name__ == "__main__":
    main()
