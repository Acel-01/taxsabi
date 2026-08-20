# Claude Code Instructions: Dataset Generation

Copy the instruction block below into Claude Code or another CLI agent that can read and write this workspace.

## Prompt A: English Augmentation

```text
You are operating as a data-engineering agent in the workspace /home/acel/afdeeptech.

Your task is to create verified English augmentation data for the NaijaTax Offline ADTC 2026 project.

Read these files before doing anything:

- adtc_2026_project_plan.md
- scripts/prompt_pack.md
- data/dataset_schema.md
- sources/SOURCE_REGISTER.md
- src/rules_engine/engine.py
- src/rules_engine/rules_ng_2026.json
- data/scenarios/train.jsonl
- data/scenarios/eval.jsonl

Do not modify the project plan, source register, rules JSON, rules engine, generated scenarios, or verifier. Do not use the evaluation scenarios for training. Do not use web search or external tax sources. Do not commit changes.

The local rules engine and each scenario's ground_truth are authoritative. You are a language-data generator, not a tax calculator. Never change, recalculate, round, or reinterpret a scenario's ground_truth. Monetary values inside ground_truth must remain strings exactly as supplied, for example "359160.00".

Generate three distinct English records for every training scenario. This is augmentation revision 2. Do not reuse or append to the existing `cloud_batch_*.jsonl` or `cloud_verified.jsonl` files. Use new output names: `cloud_v2_batch_NNN.jsonl` and `cloud_verified_v2.jsonl`.

Use IDs exactly as follows:

<scenario_id>-cloud-1
<scenario_id>-cloud-2
<scenario_id>-cloud-3

Each output record must have exactly this shape:

{
  "id": "scenario-id-cloud-1",
  "scenario_id": "scenario-id",
  "category": "calculation",
  "language": "en",
  "instruction": "natural user question",
  "output": "concise answer",
  "ground_truth": "the exact supplied ground_truth object",
  "verified_by_engine": true,
  "verification": "engine",
  "source_fact_ids": "the exact supplied source_fact_ids array",
  "scenario_family": "the exact supplied scenario_family",
  "generated_by": "cloud_llm",
  "human_reviewed": false
}

Question requirements:

- Vary wording, sentence structure, and order of facts.
- Preserve every fact in the scenario exactly.
- Do not add an unmentioned relief or financial fact.
- Clearly distinguish monthly salary from annual salary.
- Do not mention Nigeria, Nigerian, 2026, or estimated in every question.
- Make at least one variant omit country and year so the model must apply the default Nigeria/2026 scope.
- Make at least one variant use exact Nigerian shorthand such as `1.6m`, `500k`, or `300k per month`.
- Ask naturally for tax, rather than always using the phrase "estimated annual personal income tax".

Answer requirements:

- Use concise English, preferably under 250 tokens.
- State gross annual income.
- If income is monthly, show the annualization explicitly, for example `NGN 200,000 x 12 = NGN 2,400,000`.
- State deductions naturally, for example "rent relief of NGN 240,000 was applied".
- State chargeable income.
- State the exact estimated annual tax from ground_truth.
- Include the relevant NTA 2025 sections and Fourth Schedule citation.
- Mention that documentary evidence may be required under section 32.
- If country/year are omitted, state briefly that Nigeria and 2026 are being assumed.
- If country/year are explicitly outside Nigeria/2026, decline instead of calculating.
- Use NGN amounts with digits and comma separators.
- Do not invent legal claims, rates, deductions, or tax years.
- Do not use Markdown fences in the output.

Process the file in batches of 5 scenarios. For each batch:

1. Read the next five records from data/scenarios/train.jsonl.
2. Generate the 15 JSONL records in memory.
3. Write them to data/train/cloud_v2_batch_NNN.jsonl, using the next batch number for this v2 run.
4. Run this command:

   uv run python scripts/verify_dataset.py \
      data/train/cloud_v2_batch_NNN.jsonl \
     --scenario-files \
     data/scenarios/train.jsonl \
      data/scenarios/eval.jsonl \
      data/scenarios/normalization.jsonl

5. If verification fails, regenerate the failing records. Never hand-edit tax numbers or ground_truth.
6. Continue automatically with the next batch until all training scenarios are processed.

After all batches pass:

1. Combine only the verified v2 batch files into data/train/cloud_verified_v2.jsonl.
2. Ensure every record ID is unique.
3. Run the verifier on the combined file:

   uv run python scripts/verify_dataset.py \
      data/train/cloud_verified_v2.jsonl \
     --scenario-files \
     data/scenarios/train.jsonl \
      data/scenarios/eval.jsonl \
      data/scenarios/normalization.jsonl

4. Report the number of scenarios processed, records generated, records rejected, and final verification result.

Do not print all generated records in your final response. Write them to files and report a concise summary.
```

## Prompt B: Nigerian Pidgin Augmentation

Run this only after the English records pass verification and only for a small pilot batch.

```text
Using the verified English records in data/train/final_english_v5.jsonl, select 20 records from different categories and scenario families and create Nigerian Pidgin variants. Include at least five records with omitted country/year context or shorthand amounts such as `1.6m` and `500k`, and at least five explicit monthly-income records.

Read scripts/prompt_pack.md, sources/SOURCE_REGISTER.md, and data/dataset_schema.md first.

Rules:

- Do not change ground_truth, source_fact_ids, scenario_family, or any monetary value.
- Set language to "pcm".
- Do not use the repeated phrase "wey get deductible amount". Prefer natural wording such as "deduction wey apply na ..." or "rent relief na ...".
- Translate the user question and answer naturally into Nigerian Pidgin.
- Preserve NGN amounts, percentages, section numbers, and tax-band values exactly.
- If the input is monthly, show the monthly amount multiplied by 12 before stating annual income.
- Do not translate statutory citations into unsupported claims.
- Do not mark human_reviewed true; a fluent human must review these records later.
- Write records to data/train/pidgin_pilot_v2.jsonl. Preserve the existing reviewed file `pidgin_reviewed.jsonl`.
- Run:

  uv run python scripts/verify_dataset.py \
    data/train/pidgin_pilot_v2.jsonl \
    --scenario-files \
    data/scenarios/train.jsonl \
    data/scenarios/eval.jsonl

Report the verifier result and list the records that need native-speaker review.
```

## Prompt C: Dataset Audit

```text
Audit the current dataset without modifying source facts, rules, scenarios, or generated answers.

Read data/train/seed.jsonl, data/eval/seed.jsonl, data/train/cloud_verified_v2.jsonl if it exists, data/train/pidgin_pilot_v2.jsonl if it exists, and sources/SOURCE_REGISTER.md.

Run the verifier on every available dataset file. Then report:

- Record counts by file, category, language, and scenario family.
- Whether any training/evaluation scenario families overlap.
- Whether any source fact IDs are unknown or missing.
- Whether all calculation records pass Decimal ground-truth verification.
- Whether any records contain unsupported language or legal claims.
- Ten representative records for human review, identified by ID only.

Do not modify files and do not commit changes.
```
