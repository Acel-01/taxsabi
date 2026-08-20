# Dataset Schema — NaijaTax Offline

JSONL, one example per line. All training data in `data/train/`, held-out eval in `data/eval/` (never share scenario families between the two).

```json
{
  "id": "q-0001",
  "scenario_id": "train-0001",
  "category": "statutory_fact | calculation | counterfactual | clarification | scope_behavior | normalization | multilingual",
  "language": "en | pcm | yo | ha | ig",
  "instruction": "user question, natural phrasing",
  "output": "canonical answer",
  "ground_truth": {
    "gross_annual_salary": "3600000.00",
    "relief_inputs": {"rent": "1200000.00"},
    "applied_reliefs": {"rent": "240000.00"},
    "total_relief": "240000.00",
    "expected_chargeable_income": "3360000.00",
    "expected_total_tax": "394800.00",
    "tax_breakdown": []
  },
  "verified_by_engine": true,
  "verification": "engine | source_register",
  "source_fact_ids": ["F-001", "F-004"],
  "scenario_family": "salaried_tenant_pensioner",
  "generated_by": "manual | deterministic_template | cloud_llm",
  "source_verified": true,
  "human_reviewed": false
}
```

## Rules

1. `ground_truth.expected_*` fields come from the deterministic engine, never from the generating LLM. Source-only fact records use `ground_truth: null`.
2. Any generated example whose `output` does not match `ground_truth` is discarded, not corrected.
3. `scenario_family` must never appear in both `train/` and `eval/`.
4. Answers are concise (under ~250 tokens), cite sections, and include the documentation caveat where the statute requires it.
5. Every example traces to a `sources/SOURCE_REGISTER.md` fact id with status `verified_primary` or `verified_secondary`.
6. Monetary values in JSON are strings. Internal calculations use Python `Decimal`; this avoids binary floating-point rounding when records are reloaded.
7. Source-grounded non-calculation records use `source_verified: true`; language records additionally require human review before final inclusion.
