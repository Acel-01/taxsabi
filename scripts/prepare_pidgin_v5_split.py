#!/usr/bin/env python3
"""Recreate the fixed reviewed-Pidgin train/evaluation split."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_IDS = {
    "fact-f001-bands-pidgin",
    "fact-scope-country-pidgin",
    "train-clarification-period-11-pidgin",
    "train-0010-v3-pidgin",
    "train-0001-v3-pidgin",
    "train-0023-v3-pidgin",
}


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def main():
    rows = read(ROOT / "data/train/pidgin_reviewed_v2.jsonl")
    assert len(rows) == 20
    assert all(row["human_reviewed"] for row in rows)
    assert len(HOLDOUT_IDS) == 6

    evaluation = [row for row in rows if row["id"] in HOLDOUT_IDS]
    training = [row for row in rows if row["id"] not in HOLDOUT_IDS]
    assert len(evaluation) == 6
    assert len(training) == 14

    write(ROOT / "data/eval/pidgin_eval_v5.jsonl", evaluation)
    write(ROOT / "data/train/pidgin_train_v5.jsonl", training)
    print(f"wrote {len(training)} Pidgin training records")
    print(f"wrote {len(evaluation)} Pidgin evaluation records")


if __name__ == "__main__":
    main()
