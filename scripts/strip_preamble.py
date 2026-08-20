#!/usr/bin/env python3
"""Normalize calculation outputs: remove canned preambles, keep a minimal
'For Nigeria 2026:' prefix. Applies only to category == 'calculation'."""

import argparse
import json
import re

PATTERNS = [
    re.compile(
        r"^Assuming Nigeria and the 2026 year of assessment, based on the facts stated\. "
        r"This is an estimate under the Nigeria Tax Act 2025\.\s*"
    ),
    re.compile(
        r"^For Nigeria's 2026 rules, based on the facts stated\. "
        r"This is an estimate under the Nigeria Tax Act 2025\.\s*"
    ),
    re.compile(
        r"^I am treating this as a Nigeria 2026 calculation based on the facts stated\. "
        r"This is an estimate under the Nigeria Tax Act 2025\.\s*"
    ),
    re.compile(
        r"^I dey treat this as a Nigeria 2026 calculation from the facts wey you give\. "
        r"This na estimate under the Nigeria Tax Act 2025\.\s*"
    ),
    re.compile(
        r"^Assuming Nigeria and the 2026 year of assessment, based on the stated facts:\s*"
    ),
    re.compile(r"^Assuming Nigeria and 2026:\s*"),
    re.compile(r"^For Nigeria 2026:\s*"),
]


def normalize(output: str) -> tuple[str, bool]:
    changed = False
    for pattern in PATTERNS:
        if pattern.match(output):
            output = pattern.sub("", output, count=1)
            changed = True
            break
    if changed and output and output[0].islower():
        output = output[0].upper() + output[1:]
    return output.strip(), changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    total = stripped = prefixed = skipped = 0
    with open(args.input) as source, open(args.output, "w") as destination:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("category") in ("calculation", "counterfactual"):
                total += 1
                before = record["output"]
                after, changed = normalize(before)
                record["output"] = after
                record["preamble_stripped"] = changed
                if changed:
                    stripped += 1
                else:
                    prefixed += 1
            else:
                skipped += 1
            destination.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"{args.input}: {total} calculation/counterfactual outputs normalized "
        f"({stripped} stripped, {prefixed} prefixed), {skipped} other records untouched"
    )


if __name__ == "__main__":
    main()
