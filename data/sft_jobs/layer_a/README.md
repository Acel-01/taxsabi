# Layer A — English conversations (bulk)

Process every `batch_*.jsonl` in this folder, one batch at a time. For each blueprint, write a natural 3–5 turn conversation (user/assistant alternating, starting with user).

Rules:
- The `authoritative` values are computed by the local tax engine. Never change, round, or recalculate a number. Every amount the assistant states must come from the authoritative block (including tax breakdown values when shown).
- Follow the answer format: gross income -> reliefs applied with amounts -> chargeable income -> band breakdown -> total tax.
- `authoritative.tax_breakdown` entries give band, rate, taxed amount, and tax; use them for the band breakdown.
- Keep answers concise (roughly under 250 tokens). No preamble, no "Assuming Nigeria..." when the user already stated facts. Cite sections only where a specific legal claim is made.
- Types: accumulate_compute (facts build across turns, then calculate), counterfactual (show base tax, scenario tax, saving), correction (use the corrected figure immediately), clarify_compute (ask for the period before computing), topic_shift (retain facts across topic changes), scope_decline (decline out-of-scope briefly, then answer the in-scope question).
- If a blueprint has `required_terms`, the assistant text must state them (e.g. contribution rates, deadlines, caps).

Output: `data/sft_generated/layer_a/batch_NNN.jsonl`, same base name as the input file, one JSON object per line:

{"id": "<conversation_id>", "type": "<type>", "language": "en", "turns": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}], "authoritative": <copy of the blueprint authoritative block>, "source_fact_ids": [...], "scenario_id": "...", "scenario_family": "...", "generated_by": "opencode"}

JSONL only. No markdown fences. No commentary outside the JSON lines.
