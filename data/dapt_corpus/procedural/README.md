# Procedural and Planning Prose

Hand-written domain prose for Domain-Adaptive Continued Pretraining (Phase 1). These documents connect the verified legal facts to practical employee questions — computing tax, claiming reliefs, running payroll, and using pension contributions as a planning lever.

## Files

| File | Covers |
|---|---|
| `01_income_tax_basics_2026.md` | The 2026 framework, the computation chain, the bands, a worked example, the minimum wage exemption, PAYE in outline |
| `02_reliefs_and_deductions_guide.md` | The section 30 deduction list one by one, claim formality, evidence requirements, filing mechanics (e-Tax/Tax Form A, timing, refunds), common mistakes |
| `03_tax_efficiency_planning.md` | Marginal-rate reasoning, deduction value by band, relief sequencing, voluntary pension contributions as the flexible lever, worked comparisons |
| `04_paye_payroll_and_compliance.md` | Employer and employee duties, the remittance clocks (PAYE, pension, WHT), returns, payslip literacy, reconciliation/refunds, routine |
| `05_pension_and_vpc_guide.md` | Contributory Pension Scheme mechanics, mandatory and voluntary contributions, remittance rules and penalties, tax treatment, practical steps |
| `06_scope_and_boundaries.md` | What the 2026 framework covers and what changed, out-of-scope topics, the discipline behind every statement |

Note: a distilled fact sheet (bands, reliefs, deadlines in consecutive sentences) was trialled as document 07 in DAPT run 4 and caused number bleed/garbling — dense numeric facts repeated too often overfit the adapter. It now lives at `sources/KEY_FACTS_REFERENCE.md` as a reference for SFT data generation, not as DAPT text.

## Grounding

Every factual statement traces to the source register (`sources/SOURCE_REGISTER.md`). Core mappings:

| Document | Facts and sources used |
|---|---|
| 01 | F-001, F-002, F-005, F-007, F-008, F-009, F-010, F-011, F-015 |
| 02 | F-003, F-004, F-005, F-006, F-012, F-014, F-017, F-018, F-019, S5 |
| 03 | F-001, F-003, F-004, F-014, F-016, S8 (rules 3.4–3.13, 3.17, 5.1) |
| 04 | F-005, F-011, F-016, F-017, F-018, F-019, S5, S10 |
| 05 | F-003, F-013, F-014, F-016, S3 (s.4, s.10, s.11), S8 (sections 2–5) |
| 06 | F-008, F-009, F-010, F-011, F-015, S5, S6 |

Writing rules applied:

- No fact appears that is not registered; where the register marks a caveat (for example, the PAYE deadline's regulatory caveat), the prose states the working rule without overclaiming.
- No fact-ID markers appear in the prose itself — grounding is recorded here instead.
- Numbers (tax arithmetic in worked examples) are derived only from the published bands and are recomputable from F-001.

## Status

Draft for review. Not yet folded into the DAPT token stream alongside the statutes and the PenCom guidelines; once reviewed, the corpus README will track the combined size.
