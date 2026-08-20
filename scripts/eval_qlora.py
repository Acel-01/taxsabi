#!/usr/bin/env python3
"""Evaluate a fine-tuned model on a held-out JSONL dataset.

Scores:
  calc_acc        - calculation records where the amount after the answer's
                    labelled annual-tax statement matches expected_total_tax
  calc_ci_acc     - same, using the labelled chargeable-income statement

Writes <out>/report.jsonl (one scored row per record) and prints a summary.
Non-calculation records are written for manual review (report file only).

Example:
  python eval_qlora.py --model /content/models/en_qwen3_0.6b/merged \
      --eval data/eval/final_eval_v5.jsonl --out /content/models/en_qwen3_0.6b/eval.jsonl
"""
import argparse
import json
import os
import re

AMOUNT_RE = re.compile(
    r"(?<![\d,])(?:\bNGN\s*)?"
    r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)(?![\d,])",
    re.IGNORECASE,
)
TOTAL_TAX_RE = re.compile(
    r"(?:estimated\s+annual\s+tax|total\s+(?:estimated\s+)?annual\s+tax|"
    r"annual\s+tax|tax\s+due|estimated\s+tax)"
    r"\s*(?::|is|=|na)\s*(?:NGN\s*)?"
    r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
CHARGEABLE_INCOME_RE = re.compile(
    r"chargeable\s+income\s*(?::|is|=|na)\s*(?:NGN\s*)?"
    r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

def norm_amount(text):
    from decimal import Decimal

    value = Decimal(re.sub(r"[^0-9.]", "", text))
    return format(value.quantize(Decimal("0.01")), "f")

def load_jsonl(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def extract_amounts(text):
    found = []
    for num in AMOUNT_RE.findall(text):
        if norm_amount(num) != "0.00" or num in ("0", "0.0", "0.00"):
            found.append(num)
    return [norm_amount(n) for n in found]


def extract_labeled_amount(text, pattern):
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return norm_amount(matches[-1].group(1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="merged model dir")
    ap.add_argument("--eval", required=True, help="eval JSONL")
    ap.add_argument("--out", required=True, help="report JSONL path")
    ap.add_argument("--max-new-tokens", type=int, default=384)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    args = ap.parse_args()

    import torch
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_len,
        dtype=None,
        load_in_4bit=False,
    )
    FastLanguageModel.for_inference(model)

    tpl_kwargs = {}
    if getattr(model.config, "model_type", "") == "qwen3":
        tpl_kwargs = {"enable_thinking": False}

    system = (
        "You are an assistant that answers questions about Nigerian individual "
        "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
    )

    rows = load_jsonl(args.eval)
    scored = {"calc_total": 0, "calc_tax_ok": 0, "calc_ci_ok": 0}
    report = []

    for row in rows:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": row["instruction"]},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, **tpl_kwargs
        )
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
            )
        generated = out[0][inputs["input_ids"].shape[1]:]
        answer = tokenizer.decode(generated, skip_special_tokens=True).strip()

        entry = {
            "id": row["id"],
            "category": row["category"],
            "language": row.get("language", "en"),
            "instruction": row["instruction"],
            "expected": row.get("output"),
            "answer": answer,
        }
        gt = row.get("ground_truth")
        if gt and row["category"] == "calculation":
            scored["calc_total"] += 1
            amounts = extract_amounts(answer)
            expected_tax = norm_amount(gt["expected_total_tax"])
            expected_ci = norm_amount(gt["expected_chargeable_income"])
            predicted_tax = extract_labeled_amount(answer, TOTAL_TAX_RE)
            predicted_ci = extract_labeled_amount(answer, CHARGEABLE_INCOME_RE)
            entry["amounts_found"] = amounts
            entry["expected_total_tax"] = expected_tax
            entry["expected_chargeable_income"] = expected_ci
            entry["predicted_total_tax"] = predicted_tax
            entry["predicted_chargeable_income"] = predicted_ci
            tax_ok = predicted_tax == expected_tax
            ci_ok = predicted_ci == expected_ci
            entry["calc_tax_ok"] = tax_ok
            entry["calc_ci_ok"] = ci_ok
            if tax_ok:
                scored["calc_tax_ok"] += 1
            if ci_ok:
                scored["calc_ci_ok"] += 1
        report.append(entry)

    parent = os.path.dirname(args.out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, "w") as fh:
        for entry in report:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    total = scored["calc_total"]
    tax_acc = scored["calc_tax_ok"] / total if total else 0.0
    ci_acc = scored["calc_ci_ok"] / total if total else 0.0
    print(f"model: {args.model}")
    print(f"eval: {args.eval}  ->  {len(rows)} records, {total} calculations")
    if total:
        print(f"calc_acc (expected_total_tax in answer): {scored['calc_tax_ok']}/{total} = {tax_acc:.1%}")
        print(f"calc_ci_acc (expected_chargeable_income): {scored['calc_ci_ok']}/{total} = {ci_acc:.1%}")
    print("report written to", args.out)

if __name__ == "__main__":
    main()
