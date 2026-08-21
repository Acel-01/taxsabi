#!/usr/bin/env python3
"""Evaluate a GGUF model against a held-out JSONL set through llama.cpp.

Scoring mirrors eval_qlora.py: the amount after the answer's labelled
annual-tax statement must equal expected_total_tax (exact), with a second
tolerance count for answers within NGN 1.

Usage:
  1. Start the model server:
       llama-server -m model/x.gguf -c 2048 -t 4 --port 8080
  2. Run:
       uv run python scripts/eval_gguf_llamacpp.py \
         --model model/x.gguf \
         --eval data/eval/final_eval_v5_unique.jsonl \
         --out data/gguf_natural_eval.jsonl

Or pass --start-server to launch and stop llama-server automatically.
"""
import argparse
import json
import subprocess
import time
import urllib.request

from eval_qlora import (
    CHARGEABLE_INCOME_RE,
    TOTAL_TAX_RE,
    extract_labeled_amount,
)

SYSTEM = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)


def post(base: str, messages: list[dict], max_tokens: int, seed: int) -> str:
    body = json.dumps(
        {
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": max_tokens,
            "stream": False,
            "seed": seed,
        }
    ).encode()
    request = urllib.request.Request(
        base + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)["choices"][0]["message"]["content"]


def wait_for_health(base: str, timeout: int = 300) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/health", timeout=5) as response:
                if json.load(response).get("status") == "ok":
                    return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    raise SystemExit("llama-server did not become healthy in time")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="GGUF path")
    parser.add_argument("--eval", required=True, help="eval JSONL")
    parser.add_argument("--out", required=True, help="report JSONL")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=260)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--ctx-size", type=int, default=2048)
    args = parser.parse_args()

    base = f"http://127.0.0.1:{args.port}"
    server = None
    if args.start_server:
        server = subprocess.Popen(
            [
                "llama-server",
                "-m", args.model,
                "-c", str(args.ctx_size),
                "-t", str(args.threads),
                "--port", str(args.port),
                "--log-disable",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    wait_for_health(base)

    rows = [
        json.loads(line)
        for line in open(args.eval)
        if line.strip()
    ]
    report = []
    totals = {"calc": 0, "exact": 0, "tol": 0, "ci": 0}
    for row in rows:
        content = post(
            base,
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": row["instruction"]},
            ],
            max_tokens=args.max_tokens,
            seed=args.seed,
        )
        entry = {
            "id": row["id"],
            "category": row["category"],
            "language": row.get("language", "en"),
            "instruction": row["instruction"],
            "expected": row.get("output"),
            "answer": content,
        }
        if row["category"] == "calculation":
            truth = row["ground_truth"]
            expected_tax = str(truth["expected_total_tax"])
            expected_ci = str(truth["expected_chargeable_income"])
            predicted_tax = extract_labeled_amount(content, TOTAL_TAX_RE)
            predicted_ci = extract_labeled_amount(content, CHARGEABLE_INCOME_RE)
            entry.update(
                {
                    "expected_total_tax": expected_tax,
                    "expected_chargeable_income": expected_ci,
                    "predicted_total_tax": predicted_tax,
                    "predicted_chargeable_income": predicted_ci,
                    "calc_tax_ok": predicted_tax == expected_tax,
                    "calc_ci_ok": predicted_ci == expected_ci,
                }
            )
            totals["calc"] += 1
            totals["exact"] += entry["calc_tax_ok"]
            totals["ci"] += entry["calc_ci_ok"]
            if predicted_tax is not None and abs(float(predicted_tax) - float(expected_tax)) <= 1.0:
                totals["tol"] += 1
        report.append(entry)

    with open(args.out, "w") as output:
        for entry in report:
            output.write(json.dumps(entry, ensure_ascii=False) + "\n")

    total = totals["calc"]
    print(f"model: {args.model}")
    print(f"eval: {args.eval} -> {len(rows)} records, {total} calculations")
    print(
        f"calc_acc (exact): {totals['exact']}/{total} = {totals['exact'] / total:.1%}"
        if total else "no calculations"
    )
    if total:
        print(f"calc_acc (within NGN 1): {totals['tol']}/{total} = {totals['tol'] / total:.1%}")
        print(f"calc_ci_acc: {totals['ci']}/{total} = {totals['ci'] / total:.1%}")
    print(f"report written to {args.out}")

    if server is not None:
        server.terminate()


if __name__ == "__main__":
    main()
