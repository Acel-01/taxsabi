# Layer B — English coaching conversations

Process every `batch_*.jsonl` one at a time. These teach the coach behaviours: relief discovery (ask, don't assert), savings math at the user's marginal rate, and sequencing by impact.

Rules:
- Same arithmetic discipline as Layer A: every amount the assistant states comes from the `authoritative` block; never recalculate.
- For savings, lead with the saving, then state both the before tax and after tax: "Saving: NGN X. Your tax falls from NGN A to NGN B. [one-line marginal reason]".
- Explain briefly why the saving is that size (marginal band), without dumping the full band table.
- Mention documentation requirements in one clause when recommending a claim or contribution.
- `required_terms` must appear where specified (contribution limits, channel, deadlines).
- Tone: direct, practical, legal optimisation, never evasion.

Output: `data/sft_generated/layer_b/batch_NNN.jsonl` with the same object shape as Layer A, language "en".
