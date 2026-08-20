#!/usr/bin/env python3
"""Score counterfactual fields in an existing model evaluation report."""

import argparse
import json

from eval_qlora import extract_amounts, norm_amount


FIELDS = (
    "base_chargeable_income",
    "scenario_chargeable_income",
    "base_tax",
    "scenario_tax",
    "tax_saving",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--eval", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source = {
        json.loads(line)["id"]: json.loads(line)
        for line in open(args.eval)
        if line.strip()
    }
    rows = []
    total = complete = 0
    field_counts = {field: 0 for field in FIELDS}
    with open(args.report) as report_file:
        for line in report_file:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("category") == "counterfactual":
                truth = source[row["id"]]["ground_truth"]
                found = set(extract_amounts(row.get("answer", "")))
                checks = {
                    field: norm_amount(truth[field]) in found for field in FIELDS
                }
                row["counterfactual_fields"] = checks
                row["counterfactual_all_fields_ok"] = all(checks.values())
                total += 1
                complete += row["counterfactual_all_fields_ok"]
                for field, passed in checks.items():
                    field_counts[field] += passed
            rows.append(row)

    with open(args.out, "w") as output_file:
        for row in rows:
            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"counterfactual exact: {complete}/{total} = {complete / total:.1%}")
    print("fields:", field_counts)
    print("rescored report written to", args.out)


if __name__ == "__main__":
    main()
