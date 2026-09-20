# Single-turn Pidgin Q&A

Every blueprint is a 2-turn conversation: one user question, one assistant answer. Follow `data/sft_jobs/layer_c/README.md` tone rules. Write only the user question (per its `guidance` and `style`) and the assistant answer.

Answer format:
- Calculation/single_calc: "Total tax: NGN X. Gross income: NGN G. Reliefs applied: ... total relief NGN R. Chargeable income: NGN C. Band breakdown: ..."
- Counterfactual/single_counterfactual: "Saving: NGN S. Your tax drops from NGN A to NGN B. [one-line reason]"
- Fact/single_fact: concise prose; every `required_terms` item must appear verbatim (case-insensitive); no invented figures.

Number discipline: use ONLY values from the blueprint `authoritative` block; never invent, recalculate, or round. Amount format "NGN 3,000,000" (comma separators, no .00).

Method: temporary Python script via heredoc defining the question and answer per conversation_id, then merging blueprint fields (id from conversation_id, type, language, authoritative, required_terms, source_fact_ids, scenario_id, scenario_family) plus generated_by "opencode".

Do not modify other files. Do not run scripts/verify_sft_generation.py. Return one line per batch handled.
