# Layer C — Pidgin conversations

Process every `batch_*.jsonl` one at a time. Same rules as Layer A, but write the conversation in natural Nigerian Pidgin.

Rules:
- Pidgin must sound like a Nigerian person explaining tax, not English with Pidgin words sprinkled in. Keep the conversation in Pidgin throughout; do not switch to English.
- Same arithmetic discipline: every amount comes from the `authoritative` block; never recalculate.
- Keep the answer format (gross -> reliefs -> chargeable -> bands -> total tax) even in Pidgin.
- `required_terms` must appear (numbers and key terms can stay in their standard form).

Output: `data/sft_generated/layer_c/batch_NNN.jsonl` with the same object shape, language "pcm".
