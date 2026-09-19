#!/usr/bin/env python3
"""Run multi-turn conversations through a GGUF model via llama.cpp.

Maintains conversation history across turns (unlike run_baseline.py, which is
single-turn). Used to capture cross-stage behavior for the multi-turn suite.

Usage:
    uv run python scripts/run_multiturn.py \
      --model model/Qwen3-1.7B-Q4_K_M.gguf \
      --suite data/eval/multiturn_suite.jsonl \
      --out data/eval/baselines/multiturn_base_qwen3_1.7b.jsonl \
      --label base-qwen3-1.7b --start-server
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_gguf_llamacpp import wait_for_health  # noqa: E402

DEFAULT_SYSTEM = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)


def post(base: str, messages: list[dict], max_tokens: int, seed: int, thinking: bool) -> str:
    payload = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stream": False,
        "seed": seed,
        "chat_template_kwargs": {"enable_thinking": bool(thinking)},
    }
    request = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="GGUF path")
    parser.add_argument("--suite", required=True, help="multi-turn suite JSONL")
    parser.add_argument("--out", required=True, help="output capture JSONL")
    parser.add_argument("--label", required=True, help="stage label")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--ctx-size", type=int, default=4096)
    parser.add_argument("--thinking", action="store_true", help="enable thinking mode (default: off)")
    args = parser.parse_args()

    base = f"http://127.0.0.1:{args.port}"
    server = None
    if args.start_server:
        server = subprocess.Popen(
            [
                "llama-server", "-m", args.model,
                "-c", str(args.ctx_size), "-t", str(args.threads),
                "--port", str(args.port), "--no-webui", "--log-disable",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    wait_for_health(base)

    conversations = [
        json.loads(line) for line in open(args.suite) if line.strip()
    ]
    started = datetime.now(timezone.utc).isoformat()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Resume: skip conversations already present in the output (delete the file to re-capture).
    done_ids: set[str] = set()
    if out_path.exists():
        done_ids = {
            json.loads(line)["id"]
            for line in out_path.read_text().splitlines()
            if line.strip()
        }
    pending = [conv for conv in conversations if conv["id"] not in done_ids]
    if done_ids:
        print(f"resuming: {len(done_ids)} conversations already captured, {len(pending)} to go")
    # Write each conversation as it completes so an interruption keeps progress.
    total_turns = 0
    with open(out_path, "a" if done_ids else "w") as fh:
        for conv in pending:
            messages = [{"role": "system", "content": args.system_prompt}]
            captured_turns = []
            for turn in conv["turns"]:
                messages.append({"role": "user", "content": turn["user"]})
                answer = post(base, messages, max_tokens=args.max_tokens, seed=args.seed, thinking=args.thinking)
                messages.append({"role": "assistant", "content": answer})
                captured = {"user": turn["user"], "answer": answer}
                if "ground_truth" in turn:
                    captured["ground_truth"] = turn["ground_truth"]
                if "note" in turn:
                    captured["note"] = turn["note"]
                captured_turns.append(captured)
                total_turns += 1
                print(f"{conv['id']} turn {len(captured_turns)}: {answer[:70].replace(chr(10), ' ')}...", flush=True)
            record = {
                "id": conv["id"],
                "title": conv.get("title"),
                "language": conv.get("language", "en"),
                "category": conv.get("category", "multi_turn"),
                "label": args.label,
                "model": args.model,
                "thinking": args.thinking,
                "captured_at": started,
                "turns": captured_turns,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
    print(f"\ncaptured {len(conversations)} conversations, {total_turns} turns -> {args.out}")

    if server is not None:
        server.terminate()


if __name__ == "__main__":
    main()
