#!/usr/bin/env python3
"""Rescore an existing eval_qlora.py report without loading a model."""

import argparse
import json

from eval_qlora import (
    CHARGEABLE_INCOME_RE,
    TOTAL_TAX_RE,
    extract_labeled_amount,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = []
    total = tax_ok = ci_ok = 0
    with open(args.report) as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("category") == "calculation":
                total += 1
                expected_tax = row.get("expected_total_tax")
                expected_ci = row.get("expected_chargeable_income")
                predicted_tax = extract_labeled_amount(
                    row.get("answer", ""), TOTAL_TAX_RE
                )
                predicted_ci = extract_labeled_amount(
                    row.get("answer", ""), CHARGEABLE_INCOME_RE
                )
                row["predicted_total_tax"] = predicted_tax
                row["predicted_chargeable_income"] = predicted_ci
                row["calc_tax_ok"] = predicted_tax == expected_tax
                row["calc_ci_ok"] = predicted_ci == expected_ci
                tax_ok += row["calc_tax_ok"]
                ci_ok += row["calc_ci_ok"]
            rows.append(row)

    with open(args.out, "w") as destination:
        for row in rows:
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"calc_acc: {tax_ok}/{total} = {tax_ok / total:.1%}")
    print(f"calc_ci_acc: {ci_ok}/{total} = {ci_ok / total:.1%}")
    print(f"rescored report written to {args.out}")


if __name__ == "__main__":
    main()
