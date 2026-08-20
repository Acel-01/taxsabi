# Training Data Status

`cloud_verified.jsonl` and `final_english.jsonl` contain revision 1 wording. Their arithmetic is verified, but they overuse explicit country/year language and are not the final training artifacts.

Use the revision 2 flow:

1. Generate `cloud_verified_v2.jsonl` with the instructions in `scripts/claude_code_data_generation.md`.
2. Generate the balanced behavior and counterfactual records.
3. Assemble the final balanced English set:

```bash
uv run python scripts/assemble_dataset.py \
  --inputs \
  data/train/seed.jsonl \
  data/train/cloud_verified_v2.jsonl \
  data/train/behavior_en.jsonl \
  data/train/counterfactual.jsonl \
  --max-calculation 1000 \
  --output data/train/final_english_v5.jsonl
```

4. Verify `final_english_v5.jsonl` before training.

After human review, the multilingual candidate is `data/train/final_en_pcm_v5.jsonl`. Keep the English-only `final_english_v5.jsonl` as the baseline for comparison.

The mixed held-out evaluation file is `data/eval/final_eval_v5.jsonl`.
