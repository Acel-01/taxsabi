#!/usr/bin/env python3
"""Remove exact-content duplicates from an evaluation JSONL file."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = []
    seen = set()
    with open(args.input) as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            key = (
                record.get("language"),
                record.get("category"),
                record.get("instruction"),
                record.get("output"),
            )
            if key in seen:
                continue
            seen.add(key)
            records.append(record)

    with open(args.output, "w") as destination:
        for record in records:
            destination.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote {len(records)} content-unique records to {args.output}")


if __name__ == "__main__":
    main()
