#!/usr/bin/env python3
"""Capture raw model outputs for a prompt set — no scoring, just the behaviors.

Used for every training stage: base model baseline, DAPT checkpoint,
SFT checkpoint, KTO checkpoint, GRPO checkpoint. Outputs are archived so
before/after comparisons can be made across stages.

Usage:
  1. Start the model server (or pass --start-server):
       llama-server -m model/Qwen3-1.7B-Q4_K_M.gguf -c 2048 -t 4 --port 8080 --no-webui
  2. Run:
       uv run python scripts/run_baseline.py \
         --model model/Qwen3-1.7B-Q4_K_M.gguf \
         --prompts data/eval/baseline_prompts.jsonl \
         --out data/eval/baselines/base_qwen3_1.7b.jsonl \
         --label base-qwen3-1.7b

Thinking mode is disabled by default (per the locked plan). Pass --thinking
to enable it for experiments.
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_gguf_llamacpp import wait_for_health  # noqa: E402

DEFAULT_SYSTEM = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="GGUF path")
    parser.add_argument("--prompts", required=True, help="prompt JSONL")
    parser.add_argument("--out", required=True, help="output JSONL")
    parser.add_argument("--label", required=True, help="stage label, e.g. base-qwen3-1.7b")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--ctx-size", type=int, default=2048)
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

    prompts = [json.loads(line) for line in open(args.prompts) if line.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    # Resume: skip records already present in the output (delete the file to re-capture).
    done_ids: set[str] = set()
    if out_path.exists():
        done_ids = {
            json.loads(line)["id"]
            for line in out_path.read_text().splitlines()
            if line.strip()
        }
    pending = [record for record in prompts if record["id"] not in done_ids]
    if done_ids:
        print(f"resuming: {len(done_ids)} already captured, {len(pending)} to go")
    count = 0
    # Write each record as it completes so an interruption keeps progress.
    with open(out_path, "a" if done_ids else "w") as fh:
        for record in pending:
            body_messages = [
                {"role": "system", "content": args.system_prompt},
                {"role": "user", "content": record["prompt"]},
            ]
            answer = post_extended(
                base, body_messages,
                max_tokens=args.max_tokens,
                seed=args.seed,
                thinking=args.thinking,
            )
            row = {
                "id": record["id"],
                "language": record.get("language", "en"),
                "category": record.get("category", "unknown"),
                "prompt": record["prompt"],
                "answer": answer,
                "label": args.label,
                "model": args.model,
                "thinking": args.thinking,
                "captured_at": started,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            count += 1
            print(f"[{count}/{len(pending)}] {record['id']}: {answer[:70].replace(chr(10), ' ')}...", flush=True)
    print(f"\ncaptured {count} outputs -> {args.out}")

    if server is not None:
        server.terminate()


def post_extended(base: str, messages: list[dict], max_tokens: int, seed: int, thinking: bool) -> str:
    """POST with chat_template_kwargs to control thinking mode."""
    import urllib.request

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


if __name__ == "__main__":
    main()
