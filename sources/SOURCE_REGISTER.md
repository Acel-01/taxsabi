# Source Register — NaijaTax Offline

Every fact in the rules engine and training dataset must appear here first with a verification status.

Statuses: `verified_primary` (read directly in statute), `verified_secondary` (law-firm/employer-association analysis), `unverified`.

## Primary sources

| Ref | Document | Location |
|---|---|---|
| S1 | Nigeria Tax Act 2025 (edited for 2026), 215 pp. | `sources/tax_act_2025.txt` (extracted; original PDF in repo root) |
| S2 | NHF Act 1992, s.4, as amended by Business Facilitation (Miscellaneous Provisions) Act 2022, s.45 | secondary: NECA circular 24 Mar 2023; TEMPLARS client alert 12 Apr 2023 |

## Verified facts

### F-001 Individual income tax bands

Fourth Schedule (s.58), NTA 2025 — extracted text lines ~6815-6824, verbatim:

> (a) First N800,000 at 0% ; (b) Next N2,200,000 at 15% ; (c) Next N9,000,000 at 18% ; (d) Next N13,000,000 at 21% ; (e) Next N25,000,000 at 23% ; and (f) Above N50,000,000 at 25%.

Status: `verified_primary`. Cumulative boundaries: 800k, 3.0M, 12.0M, 25.0M, 50.0M.

### F-002 Chargeable income definition

s.30(1): chargeable income = total income (s.28) less eligible deductions.

Status: `verified_primary` (extracted text line ~1220).

### F-003 Eligible deductions (s.30(2)(a))

(i) NHF contributions; (ii) NHIS contributions; (iii) Pension Reform Act contributions; (iv) interest on loans for developing an owner-occupied residential house; (v) life insurance / deferred annuity premiums (self or spouse); (vi) rent relief.

Status: `verified_primary` (lines 1224-1239).

### F-004 Rent relief

s.30(2)(a)(vi): "rent relief of 20% of annual rent paid, subject to a maximum of N500,000, whichever is lower, provided that the individual accurately declares the actual amount of rent paid and other relevant information as may be prescribed by the relevant tax authority."

Status: `verified_primary` (lines 1234-1237).

### F-005 Documentation requirement

s.31-32 area: deductions must be claimed in writing; relevant tax authority may require documentary evidence and may refuse/reduce deductions where evidence is inadequate or absent.

Status: `verified_primary` (line ~1246 "Deduction shall not be allowed... unless claimed in writing..."). Confirm exact section number during rules JSON authoring.

### F-006 NHF contribution obligation (private vs public sector)

Private sector: voluntary ("may contribute"). Public sector: mandatory. Authority: NHF Act 1992 s.4 as amended by BFA 2022 s.45.

Status: `verified_secondary` (NECA circular 24 Mar 2023; TEMPLARS 12 Apr 2023). NTA 2025 itself is silent on the obligation — the Act mentions NHF exactly once, as a deduction (F-003(i)).

### F-007 Worked example

Gross 3,600,000; deductions 438,000 → chargeable 3,162,000 → tax 359,160.

Status: `verified_primary` (recomputed from F-001 bands; matches BizEdge worked example cited in early research).

## Open items

- None blocking. Lagos-specific procedural details (LIRS) deferred from Gate 1 scope.
