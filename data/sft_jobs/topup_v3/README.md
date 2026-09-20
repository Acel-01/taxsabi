# Top-up v3 — targeted drills

Single-turn records (2 turns each: one user question, one assistant answer). Follow `data/sft_jobs/single_en/README.md` rules.

Answer format (working first, total LAST):
- single_calc: "Gross income: NGN G. Reliefs applied: ... total relief NGN R. Chargeable income: NGN C. Band breakdown: ... Total tax: NGN X."
- single_counterfactual: "Your tax drops from NGN A to NGN B. [one-line reason] Saving: NGN S."
- clarify_ask: the assistant must ASK whether the amount is monthly or annual (the required terms "monthly" and "annual" must both appear); do NOT compute.
- single_fact: concise answer; every `required_terms` string must appear verbatim; no invented figures.

If a blueprint has `user_text`, the user question must be exactly that text (no rewording).
Number discipline: use ONLY values from the blueprint `authoritative` block; never invent/recalculate/round. For single_calc, apply the rent relief rule exactly as the engine did (20% of rent, capped at NGN 500,000) - never deduct the full rent unless the applied relief equals it. Amount format "NGN 3,000,000".

Method: temporary Python script via heredoc defining question and answer per conversation_id, merging blueprint fields (id from conversation_id, type, language, authoritative, required_terms, source_fact_ids, scenario_id, scenario_family) + generated_by "opencode". Pidgin records must be natural Nigerian Pidgin.

Do not modify other files. Do not run scripts/verify_sft_generation.py. Return one line per batch.
