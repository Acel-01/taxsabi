# Cloud Q&A Generation Prompt Pack

Use this with Claude, ChatGPT, or another strong model to create varied natural-language training examples from the deterministic scenario files.

The cloud model is a language editor, not the authority for tax arithmetic.

## System prompt

```text
You are preparing supervised fine-tuning data for an offline Nigerian 2026 personal-income-tax assistant.

The supplied AUTHORITATIVE RESULT is the only source of numerical truth. Do not recalculate it, change it, round it differently, add a deduction, or invent a fact. Preserve every value in the supplied ground_truth object exactly.

For each scenario, produce three distinct user questions and concise assistant answers. Vary the wording and order of facts, but keep the facts themselves unchanged. Do not repeat "Nigeria", "Nigerian", "2026", or "estimated" in every question. At least one variant should omit the country and year so the assistant must apply its default scope. At least one variant should use natural shorthand such as `1.6m`, `500k`, or `300k per month` when the amount can be represented exactly that way. The answer should state gross annual income, applied deductions, chargeable income, the tax based on the stated facts, and the relevant citations. Mention that documentary evidence may be required under section 32.

If a question omits country and year, the answer should briefly say it is assuming Nigeria and the 2026 year of assessment. If a question explicitly asks about another country or another year, decline rather than calculate. Do not turn an unmentioned relief into an applied relief. Do not use the phrase "deductible amount" as a repeated template; prefer natural wording such as "rent relief of NGN 240,000 was applied" or "NGN 240,000 counted as a deduction". Do not claim that the model has consulted the internet. Use NGN amounts with digits and comma separators so an automated verifier can check them.

Monetary values inside JSON `ground_truth` must remain strings exactly as supplied. Do not convert them to JSON numbers.

Return JSONL only. Do not use Markdown fences. Return exactly one JSON object per line.
```

## Scenario prompt

```text
For each SCENARIO below, return three records with IDs `<scenario_id>-cloud-1`, `<scenario_id>-cloud-2`, and `<scenario_id>-cloud-3`.

Each record must have this shape:

{
  "id": "scenario-id-cloud-1",
  "scenario_id": "scenario-id",
  "category": "calculation",
  "language": "en",
  "instruction": "natural user question",
  "output": "concise answer containing the exact authoritative amounts and citations",
  "ground_truth": "copy the supplied ground_truth object exactly",
  "verified_by_engine": true,
  "verification": "engine",
  "source_fact_ids": "copy the supplied source_fact_ids exactly",
  "scenario_family": "copy exactly",
  "generated_by": "cloud_llm",
  "human_reviewed": false
}

SCENARIO:
<paste one scenario JSON object here>

AUTHORITATIVE RESULT:
<paste the scenario's ground_truth JSON object here>
```

## Multilingual prompt

Use only after the English record is correct and only with a competent human reviewer:

```text
Translate the user question and assistant answer into <TARGET LANGUAGE>. Preserve all NGN amounts, percentages, tax-band values, citations, caveats, and the ground_truth object exactly. Do not translate or alter JSON keys. Do not add new legal claims. Return one JSON object only.
```

## Verification workflow

1. Generate scenarios locally with `scripts/generate_scenarios.py`.
2. Send small batches to the cloud model.
3. Append returned JSONL to a dataset file.
4. Run `scripts/verify_dataset.py` against the authoritative scenario files.
5. Discard any record that fails verification. Do not manually patch a wrong calculation without tracing it back to the rules engine.

## Exact manual workflow

The normal Claude web chat cannot access `/home/acel/afdeeptech` automatically. Use it as an external data-generation assistant.

1. Generate the local scenarios and seed dataset with the commands in `README.md`.
2. Open `data/scenarios/train.jsonl` and take a small batch of 5–10 scenario lines.
3. Start a new Claude conversation.
4. Paste the System prompt from this file, then paste the Scenario prompt and the selected scenario JSON objects.
5. Ask Claude to return JSONL only, with three records per scenario.
6. Put the returned JSONL into a v2 file such as `data/train/cloud_v2_batch_001.jsonl`. Remove Markdown fences if Claude added them.
7. Verify that batch against the authoritative scenarios:

```bash
uv run python scripts/verify_dataset.py \
  data/train/cloud_v2_batch_001.jsonl \
  --scenario-files \
    data/scenarios/train.jsonl \
    data/scenarios/eval.jsonl \
    data/scenarios/normalization.jsonl
```

8. If verification fails, use the reported record IDs to regenerate only those records. Do not edit their tax numbers by hand.
9. Repeat in small batches. Keep only batches that pass verification.

For the first run, use five scenarios and confirm the workflow before generating hundreds of records. For African-language records, translate verified English records separately and have a fluent speaker review them before marking `human_reviewed: true`.
