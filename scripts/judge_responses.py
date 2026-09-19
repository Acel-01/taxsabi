#!/usr/bin/env python3
"""LLM-judge scaffold for behavioral evaluation against the constitution.

Feeds each captured answer (single-turn or multi-turn) to a judge model with
the TaxSabi constitution as the rubric, and records dimension scores plus a
desirable/undesirable verdict. Any judge serving an OpenAI-compatible
/chat/completions endpoint works: a local llama-server, Ollama, or a hosted
API.

Usage:
    # dry run: write the judge prompts for inspection, no calls
    uv run python scripts/judge_responses.py \
      --captures data/captures/coach_sft.jsonl \
      --out data/captures/coach_sft_judged.jsonl \
      --dry-run

    # live: judge against a local server (e.g. a bigger GGUF on port 8081)
    uv run python scripts/judge_responses.py \
      --captures data/captures/coach_sft.jsonl \
      --out data/captures/coach_sft_judged.jsonl \
      --endpoint http://127.0.0.1:8081/v1 --model judge-model.gguf

Scores per record (0-5): arithmetic, citations, clarification, scope,
coaching, multi_turn, format, language. Per the constitution's usage notes,
violations of sections 1-4 make a response undesirable automatically.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIMENSIONS = [
    "arithmetic",
    "citations",
    "clarification",
    "scope",
    "coaching",
    "multi_turn",
    "format",
    "language",
]

SYSTEM_PROMPT = """You are the evaluation judge for TaxSabi, a Nigerian personal income tax assistant. You score assistant responses strictly against the constitution provided by the user. You do not answer tax questions yourself. You return only a single JSON object, no prose, no code fences."""

JUDGE_TEMPLATE = """## Rubric (TaxSabi Constitution)

{rubric}

## Evaluation task

Score the assistant response below against the rubric. Use 0-5 for each dimension (0 = severe violation, 5 = fully compliant). Use null for multi_turn when the conversation is a single turn. A violation of sections 1-4 (arithmetic, citations, clarification, scope) makes the response undesirable regardless of other scores.

{expected_block}## Conversation

{conversation}

## Required output (JSON only)

{{
  "arithmetic": 0-5,
  "citations": 0-5,
  "clarification": 0-5,
  "scope": 0-5,
  "coaching": 0-5,
  "multi_turn": 0-5 or null,
  "format": 0-5,
  "language": 0-5,
  "violations": ["short descriptions, empty if none"],
  "verdict": "desirable" | "undesirable",
  "rationale": "one or two sentences"
}}"""


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_rubric(path: Path) -> str:
    return path.read_text().strip()


def conversation_text(record: dict) -> str:
    if "turns" in record:
        lines = []
        for index, turn in enumerate(record["turns"], 1):
            lines.append(f"[turn {index}] USER: {turn['user']}")
            lines.append(f"[turn {index}] ASSISTANT: {turn.get('answer', '')}")
        return "\n".join(lines)
    prompt = record.get("prompt") or record.get("instruction", "")
    answer = record.get("answer", "")
    return f"USER: {prompt}\nASSISTANT: {answer}"


def expected_block(record: dict) -> str:
    parts = []
    if record.get("checklist"):
        parts.append("Expected elements (from the eval design):")
        parts.extend(f"- {item}" for item in record["checklist"])
    truth = record.get("ground_truth")
    if not truth and "turns" in record:
        truths = [t["ground_truth"] for t in record["turns"] if "ground_truth" in t]
        if truths:
            truth = truths
    if truth:
        parts.append(f"Engine ground truth: {json.dumps(truth, ensure_ascii=False)}")
    return ("\n".join(parts) + "\n\n") if parts else ""


def build_judge_prompt(record: dict, rubric: str) -> list[dict]:
    user = JUDGE_TEMPLATE.format(
        rubric=rubric,
        expected_block=expected_block(record),
        conversation=conversation_text(record),
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def call_judge(endpoint: str, model: str, messages: list[dict], api_key: str | None) -> str:
    payload = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 600,
        "stream": False,
    }
    if model:
        payload["model"] = model
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)["choices"][0]["message"]["content"]


def parse_judge_output(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in judge output")
    data = json.loads(cleaned[start : end + 1])
    for dimension in DIMENSIONS:
        value = data.get(dimension)
        if value is not None and not isinstance(value, (int, float)):
            data[dimension] = None
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", required=True, type=Path, help="capture JSONL to judge")
    parser.add_argument("--out", required=True, type=Path, help="judged results JSONL")
    parser.add_argument("--rubric", type=Path, default=ROOT / "CONSTITUTION.md")
    parser.add_argument("--endpoint", help="OpenAI-compatible base URL, e.g. http://127.0.0.1:8081/v1")
    parser.add_argument("--model", default="", help="judge model name")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--dry-run", action="store_true", help="write judge prompts only, no calls")
    parser.add_argument("--limit", type=int, default=0, help="judge only the first N records")
    parser.add_argument("--prompts-out", type=Path, help="where to write dry-run prompts (default: <out>.prompts.jsonl)")
    args = parser.parse_args()

    rubric = load_rubric(args.rubric)
    records = load_jsonl(args.captures)
    if args.limit:
        records = records[: args.limit]

    dry_run = args.dry_run or not args.endpoint
    prompts_path = args.prompts_out or Path(str(args.out) + ".prompts.jsonl")

    results = []
    if dry_run:
        if not args.endpoint and not args.dry_run:
            print("no --endpoint given; writing prompts only")
        with open(prompts_path, "w") as fh:
            for record in records:
                messages = build_judge_prompt(record, rubric)
                fh.write(json.dumps({"id": record["id"], "messages": messages}, ensure_ascii=False) + "\n")
        print(f"dry run: wrote {len(records)} judge prompts -> {prompts_path}")
        return

    for record in records:
        messages = build_judge_prompt(record, rubric)
        try:
            raw = call_judge(args.endpoint, args.model, messages, args.api_key)
            scores = parse_judge_output(raw)
            status = "ok"
        except Exception as error:  # noqa: BLE001
            scores = {}
            status = f"error: {error}"
        results.append({"id": record["id"], "status": status, "scores": scores})
        print(f"{record['id']}: {status}" + (f" verdict={scores.get('verdict')}" if scores else ""))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        for row in results:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = summarize(results)
    summary_path = Path(str(args.out) + ".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\njudged {len(results)} records -> {args.out}")
    print(f"summary -> {summary_path}")
    print(json.dumps(summary, indent=2))


def summarize(results: list[dict]) -> dict:
    ok = [r for r in results if r["status"] == "ok" and r["scores"]]
    summary: dict = {"records": len(results), "judged": len(ok)}
    for dimension in DIMENSIONS:
        values = [
            r["scores"].get(dimension)
            for r in ok
            if isinstance(r["scores"].get(dimension), (int, float))
        ]
        summary[dimension] = round(sum(values) / len(values), 2) if values else None
    verdicts = [r["scores"].get("verdict") for r in ok]
    summary["desirable"] = verdicts.count("desirable")
    summary["undesirable"] = verdicts.count("undesirable")
    summary["violations"] = sum(len(r["scores"].get("violations") or []) for r in ok)
    return summary


if __name__ == "__main__":
    main()
