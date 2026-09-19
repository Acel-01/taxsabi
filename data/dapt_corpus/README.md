# DAPT Corpus — Nigerian Tax Statutes

Source texts for Domain-Adaptive Continued Pretraining (Phase 1).

## Files

| File | Description |
|---|---|
| `tax_act_2025_clean.txt` | Nigeria Tax Act 2025 — cleaned statute text, 428,778 chars, 8,256 lines |
| `ntaa_2025_clean.txt` | Nigeria Tax Administration Act 2025 — cleaned statute text, 187,277 chars |
| `pencom_vc_guidelines_2018_clean.txt` | PenCom Voluntary Contribution Guidelines (2018) — cleaned regulator text, 28,892 chars |
| `procedural/` | Hand-written procedural/planning prose — 6 documents, 50,390 chars (see its README for grounding) |
| `README.md` | This document |

**Combined corpus: ~695,000 chars** (target range 500KB–2MB).

## Provenance

| Document | Origin | Cleaner |
|---|---|---|
| Nigeria Tax Act 2025 (No. 7, 26 June 2025) | `sources/tax_act_2025.txt` (extracted from the official print PDF) | `scripts/clean_tax_act.py` |
| Nigeria Tax Administration Act 2025 (No. 5, 26 June 2025) | `lirs.gov.ng/assets/docs/NTAA_2025.pdf` (official gazette via LIRS) | `scripts/clean_ntaa.py` |
| PenCom, Guidelines on Voluntary Contribution under the CPS (2018) | `pencom.gov.ng` PDF, extracted to `sources/pencom_vc_guidelines_2018.txt` | `scripts/clean_pencom_vc.py` |

Cleaning performed 2026-09-19. All cleaners are deterministic and re-runnable.

## Artifacts Fixed

The PDF extraction produced several artifact classes, all removed or repaired:

| Artifact | Tax Act | NTAA | Method |
|---|---:|---:|---|
| Gazette page headers | 215 | 93 | Regex line removal |
| Hyphenated line breaks (`Commence-\nment`) | 529 | 35 | Join; hyphen kept only for compounds appearing mid-line elsewhere |
| Line-break word fragments (`T\nAX`, `Shor\nt`, `pr\nduced`) | 11 | — | Curated replacements |
| Broken words with spaces (`T ax`, `S tatus`, `Pr ofits`, `Par t`) | — | — | Curated replacements |
| CAPS heading splits (`V AT` → `VAT`, `O NE` → `ONE`) | — | 27 | Curated / regex (Roman numerals protected) |
| Extract typo `ENECTED` → `ENACTED` | 1 | — | Curated replacement |

## Verification Sweep

After cleaning, both scripts re-scan for every known artifact pattern:
all classes report zero remaining in both documents, except two intentional
`S/N` table headers (`S/N AGENCY`, `S/N MINERALS`) in the Tax Act which are
correct text and protected. Roman numerals (`PART I`, `Part I of`, `X of`)
confirmed intact in both documents.

## Spot-Checked Passages

- **Fourth Schedule (bands):** `First N800,000 at 0%; Next N2,200,000 at 15%; ...` — correct
- **Section 30(2)(a)(vi) rent relief:** `rent relief of 20% of annual rent paid, subject to a maximum of N 500,000` — correct
- **Enacting clause:** `ENACTED by the National Assembly...` — repaired
- **NTAA s.14(1):** `An employer shall file a return with the relevant tax authority for all emoluments paid to its employees, not later than 31st January of each year` — correct
- **NTAA s.107(1):** remittance deadline `by the 21st day of the month immediately succeeding the month in which the amount was deducted` — correct

## Known Minor Residue

- Naira is written gazette-style as `N800,000` (no currency normalization applied —
  deliberate: the model should see the statute's authentic form alongside our
  training data's `NGN 800,000` style)
- A few hard line-wraps separate `N` from amounts in body text (`N\n500,000`) — acceptable for LM training
- `subsection` spelled without hyphen in merged line breaks, matching the Act's dominant style (112 mid-line occurrences vs 3 hyphenated)

## Still To Come (Phase 0.3)

- [x] Expanded source register — primary facts F-008..F-015 added; all pending facts resolved (P-001 → F-014, P-002 → F-015, P-006 → F-011 caveat)
- [x] Procedural source obtained — PenCom VPC Guidelines added to the corpus (2018; procedure, eligibility, 1/3-salary cap, 5-year tax rule)
- [x] Procedural/planning prose written — `procedural/` (6 documents, 50,390 chars, grounded in F-001…F-019 incl. filing mechanics/refunds); draft pending review
- [ ] 10–20% general-text replay mix
- [ ] License check
