# Source Register — TaxSabi

Every fact in the rules engine, DAPT corpus, and training dataset must appear here first with a verification status.

Statuses: `verified_primary` (read directly in statute), `verified_secondary` (law-firm/employer-association analysis), `pending` (identified, not yet verified — must not enter training data).

## Primary sources

| Ref | Document | Location |
|---|---|---|
| S1 | Nigeria Tax Act 2025 (Act No. 7, gazette 26 June 2025; effective 1 January 2026), 215 pp. | `sources/tax_act_2025.txt`; cleaned text at `data/dapt_corpus/tax_act_2025_clean.txt` |
| S2 | NHF Act 1992, s.4, as amended by Business Facilitation (Miscellaneous Provisions) Act 2022, s.45 | secondary: NECA circular 24 Mar 2023; TEMPLARS client alert 12 Apr 2023 |
| S3 | Pension Reform Act 2014 (Act text) | `sources/pra_2014_ocr.txt` — OCR of the PenCom gazette scan (`scripts/ocr_pra_2014.py`); the PDF's invisible text layer is scrambled, so pages are rendered and re-OCR'd |
| S4 | National Minimum Wage Act 2024 (wage amount) | content verified via S9 + S7 |
| S5 | LIRS Frequently Asked Questions (regulator publication) | `sources/lirs_faq_2026-09-19.txt` (from https://lirs.gov.ng/faq) |
| S6 | Nigeria Tax Administration Act 2025 (Act No. 5, gazette 26 June 2025) | `data/dapt_corpus/ntaa_2025_clean.txt` (downloaded from `lirs.gov.ng/assets/docs/NTAA_2025.pdf`) |
| S7 | Nigeria Open Data statute-register summaries — PRA 2014; National Minimum Wage Act 2024 (aggregator) | `sources/nigeriaopendata_pra_summary.txt`, `sources/nigeriaopendata_minwage_summary.txt` |
| S8 | PenCom, Guidelines on Voluntary Contribution under the Contributory Pension Scheme (2018), 18 pp. | `sources/pencom_vc_guidelines_2018.txt` (from `pencom.gov.ng` PDF) |
| S9 | National Minimum Wage (Amendment) Bill 2024 (PLAC copy), 3 pp. | `sources/min_wage_bill_2024.pdf`; s.3(1) verbatim: "national minimum wage of not less than N70,000.00 per month" |
| S10 | Deduction of Tax at Source (Withholding) Regulations, 2024 — S.I. No. 34, Gazette No. 168, Vol. 111 (2 October 2024), 14 pp. | `sources/dtos_regulations_2024_gazette.pdf` + `sources/dtos_regulations_2024_gazette.txt`; reg. 7(1): FIRS 21st / state CGT+PAYE 10th / state other 30th |
| S11 | PwC Nigeria highlights of the DToS Regulations 2024 (law-firm analysis) | `sources/dtos_regulations_2024_pwc_highlights.pdf` (+ extracted `.txt`) — used for cross-checking; superseded by S10 for operative wording |

## Verified facts (primary)

### F-001 Individual income tax bands

Fourth Schedule (s.58), NTA 2025, verbatim:

> (a) First N800,000 at 0%; (b) Next N2,200,000 at 15%; (c) Next N9,000,000 at 18%; (d) Next N13,000,000 at 21%; (e) Next N25,000,000 at 23%; and (f) Above N50,000,000 at 25%.

Status: `verified_primary` (cleaned text, Fourth Schedule). Cumulative boundaries: 800k, 3.0M, 12.0M, 25.0M, 50.0M.

### F-002 Chargeable income definition

s.30(1): chargeable income = total income (s.28) less eligible deductions.

Status: `verified_primary` (cleaned text, s.30(1)).

### F-003 Eligible deductions (s.30(2)(a))

Exact list, verbatim:

> (i) the individual's contributions under the National Housing Fund, (ii) the individual's contributions under the National Health Insurance Scheme, (iii) the individual's contributions under the Pension Reform Act, (iv) interest on loans for developing an owner-occupied residential house, (v) annual amount of any annuity or premium paid by the individual during the year preceding the year of assessment in respect of insurance on his life or the life of his spouse, or contract for a deferred annuity on his own life or the life of his spouse; (vi) rent relief ...

Status: `verified_primary` (cleaned text, s.30(2)(a)).

### F-004 Rent relief

s.30(2)(a)(vi), verbatim:

> rent relief of 20% of annual rent paid, subject to a maximum of N500,000, whichever is lower, provided that the individual accurately declares the actual amount of rent paid and other relevant information as may be prescribed by the relevant tax authority

Status: `verified_primary` (cleaned text, s.30(2)(a)(vi)).

### F-005 Deduction claim formality and proof

s.31, verbatim:

> Deduction shall not be allowed under this Part to any person for a year of assessment, unless claimed in writing in such form as the relevant tax authority may prescribe.

s.32(1), verbatim:

> The relevant tax authority may require a claimant to a deduction under section 30 (2) (a) of this Act to produce such documentary evidence as may be necessary in support of any claim and in the absence of such evidence, or where such evidence is inadequate, the relevant tax authority may refuse to allow the deduction or such part of the amount claimed.

Status: `verified_primary` (cleaned text, s.31–32).

### F-006 NHF contribution obligation (private vs public sector)

Private sector: voluntary ("may contribute"). Public sector: mandatory. Authority: NHF Act 1992 s.4 as amended by BFA 2022 s.45.

Status: `verified_secondary` (NECA circular 24 Mar 2023; TEMPLARS 12 Apr 2023). NTA 2025 itself is silent on the obligation — the Act mentions NHF only as a deduction (F-003(i)).

### F-007 Worked example

Gross 3,600,000; deductions 438,000 → chargeable 3,162,000 → tax 359,160.

Status: `verified_primary` (recomputed from F-001 bands; matches BizEdge worked example cited in early research).

### F-008 Act application and commencement

s.2, verbatim:

> This Act applies throughout Nigeria to any person required to comply with any provision of the tax laws whether personally or on behalf of another person.

Enacting formula, verbatim: `[1st January, 2026]` — the Act's commencement date.

Status: `verified_primary` (cleaned text, s.2 + enacting clause). The 2026 year of assessment begins 1 January 2026.

### F-009 Minimum wage exemption

s.58, verbatim:

> The income tax payable on the chargeable income of an individual, other than an individual earning the Minimum Wage in line with the Minimum Wage Act, in respect of each year of assessment, shall be as specified in the Fourth Schedule to this Act.

Status: `verified_primary` (cleaned text, s.58). Individuals earning the national minimum wage are exempt from income tax. The wage amount itself is set by the Minimum Wage Act (see F-015).

### F-010 No consolidated relief allowance

The NTA 2025 contains no "personal relief" or "consolidated relief allowance" concept (0 occurrences in the full text). Individual relief is delivered through the N800,000 zero-rate band (F-001) plus the s.30(2)(a) eligible deductions (F-003).

Status: `verified_primary` (full-text search of cleaned Act text). Corroborated by S5 (LIRS): "the erstwhile Consolidated Relief Allowance (CRA) has been replaced with a rent-based allowance and other eligible deductions." Relevant because older Nigerian tax guidance still describes the PITA-era CRA, which no longer applies.

### F-011 PAYE administration

Verified against the primary statute (S6, NTAA 2025), verbatim:

- **s.13(1):** "A return of income shall be filed, in the prescribed form, with the relevant tax authority in each year of assessment and without notice or demand, by — (a) every taxable person whether or not liable to pay tax; and (b) non-resident persons liable to pay tax in Nigeria under Chapter Two of the Nigeria Tax Act."
- **s.14(1):** "An employer shall file a return with the relevant tax authority for all emoluments paid to its employees, not later than 31st January of each year in respect of all employees in its employment in the preceding year."
- **s.14(2):** returns disclose gross emoluments (including allowances and benefits in kind), total deductions, net emoluments, and tax deducted for each employee.
- **s.14(3):** employees still file an annual return of income from all sources, including employment income, per s.13.
- **s.28:** "Every person who has an obligation to deduct and remit tax under this Act or any other tax legislation shall render monthly returns to the appropriate tax authority."
- **s.51(6):** "Income tax chargeable on an employee whether or not the assessment has been made, shall be deducted from any emolument payable, or from any payment made on account of the emolument, by the employer to the employee."
- **s.51(7):** the employer must ensure aggregate deductions across the year equal the employee's income tax for that year.
- **s.51(9):** "regulations relating to deduction of tax at source shall apply" — the exact rates and remittance timing are delegated to the **Deduction of Tax at Source Regulations**.
- **s.107(1):** failure to remit "by the 21st day of the month immediately succeeding the month in which the amount was deducted" triggers liability for the unremitted amount, a 10% per annum administrative penalty, and interest at the CBN monetary policy rate.

Status: `verified_primary` (S6) for the framework and obligations; remittance schedule `verified_primary` via S10 (reg. 7(1)).

**Deadline resolution (now `verified_primary` via S10):** Deduction of Tax at Source (Withholding) Regulations, 2024, reg. 7(1), verbatim:

> (a) in the case of payment to the Federal Inland Revenue Service, not later than the 21st day of the month following the month of payment; and (b) in the case of payment to a State Internal Revenue Service — (i) with respect to Capital Gains Tax and Pay-As-You-Earn, not later than the 10th day of the month following the payment, and (ii) with respect to any other deduction, not later than the 30th day of the month following the month of payment.

So PAYE remitted to a state internal revenue service is due the **10th day of the following month** — primary regulation text, corroborated by S5 (LIRS FAQ) and S11 (PwC cross-check). NTAA s.107(1)'s 21st-day trigger is the general deduction-at-source penalty framework. Three distinct clocks: **PAYE 10th** (S10/S5); **pension 7 working days from pay day** (F-016); **WHT 21st federal / 30th state** (S10). (Note: the Regulations' explanatory note states they replace prior deduction rules "other than Pay-As-You-Earn tax"; reg. 7(1)(b)(i) nonetheless fixes the PAYE remittance timeline.)

### F-012 Evidence required for relief claims (filing practice)

Per S5 (LIRS): when filing returns, evidence of contributions/payments is required for Pension, Life Assurance Premium, NHIS, and NHF — "these are mandatory for relevant reliefs to be granted." Supporting documents must be uploaded with the return (Tax Form A, financial statements where applicable, tax computation, evidence of taxes paid at source).

Status: `verified_secondary` (S5). Complements F-005 (statutory basis for evidence requirements).

### F-013 Pension and gratuity exemption

NTA 2025 s.162(1), verbatim:

> (h) pension funds and assets created under the Pension Reform Act;
> (i) pension, gratuity or any retirement benefits granted in accordance with the Pension Reform Act;

Status: `verified_primary` (cleaned Act text, s.162(1)). Note: S5 cites "Section 163(1)" for this exemption — our primary text shows the exemptions under s.162(1); the primary text governs. Pension income is exempt; pensioners remain taxable on other income (per S5).

### F-014 Pension contributions and voluntary contributions (VPC)

PRA 2014 s.4, verbatim (S3 OCR of the gazette scan, spot-checked against the rendered page):

> (1) The contribution for any employee to which this Act applies shall be made in the following rates relating to his monthly emoluments — (a) a minimum of ten per cent by the employer; and (b) a minimum of eight per cent by the employee.
>
> (2) The rates of contribution mentioned in subsection (1) … may, upon agreement between any employer and employee, be revised upwards … and the Commission shall be notified of such revision.
>
> (3) Any employee to whom this Act applies may, in addition to the total contributions being made by him and his employer, make voluntary contributions to his retirement savings account.
>
> (4)(b) … the employer's contribution shall not be less than 20 percent of the monthly emoluments of the employee [where the employer elects to bear the full responsibility of the Scheme].
>
> (7) Subject to such guidelines as may be issued, from time to time by the Commission, the categories of persons covered under section 2(3) of this Act or persons exempted under section 5 of this Act shall be entitled to make voluntary contributions under the Scheme.

PRA 2014 s.10(4), verbatim (spot-checked against the rendered page):

> any income earned on any voluntary contribution made under section 4 (3) of this Act shall be subject to tax at the point of withdrawal where the withdrawal is made before the end of 5 years from the date the voluntary contribution was made.

Tax deductibility: s.10(1) — contributions "shall form part of tax deductible expenses in the computation of tax payable by an employer or employee under the relevant income tax law"; consistent with NTA s.30(2)(a)(iii) (F-003). (The gazette print reads "under this Bill t" in s.10(1) — a print artifact; meaning is unambiguous.)

Voluntary contribution procedure (S8, PenCom Guidelines sections 2–3):
- **Eligibility (s.2):** employees in organisations with 3+ staff already making mandatory CPS contributions; CPFA/AES workers and retirees; CPS/defunct-DBS retirees with contract employment; constitutional-office categories.
- **Rules (s.3):** Naira only; remitted into/withdrawn from a licensed PFA-managed RSA; contributor notifies employer **in writing** of intention and amount; VC must be **from legitimate income and not more than one-third of the month's salary** (Labour Act 1990); all VCs remitted **through the employer** into the RSA.
- **Tax process (s.3.28–3.30):** restates the s.10(4) five-year rule with the administrative treatment.

Status: `verified_primary` for the Act sections (S3 OCR; s.4 and s.10 passages spot-checked against the rendered scan). `verified_secondary` for operating details that live only in S8 (1/3-salary cap, in-writing notice, employer-channel remittance, documentation). Caveat: S8 (2018) cites the PITA graduated table for taxing early VPC withdrawals — PITA is repealed; the 5-year rule stands, but corpus prose must map the tax treatment to the NTA 2025 (F-001/F-002).

### F-015 National minimum wage amount

National Minimum Wage (Amendment) Act 2024, s.3(1), verbatim:

> Every employer shall pay a national minimum wage of not less than N70,000.00 per month to every worker under his establishment, except otherwise provided under this Act.

Also: the minimum wage review cycle was reduced from five years to three (s.3(4) insert). Corroborated by S7: "raised the national minimum wage from N30,000 to N70,000/month." This resolves the amount referenced by F-009.

Status: `verified_secondary` (S9 bill text as published by PLAC, enacted 2024; S7 corroboration). Gazette of the signed Act not yet read — amount is not in dispute.

### F-016 Pension contribution remittance and penalties (employer duty)

PRA 2014 s.11, verbatim (S3 OCR, spot-checked against the rendered page):

> (3) The employer shall — (a) deduct at source the monthly contribution of the employee; and (b) not later than 7 working days from the day the employee is paid his salary, remit an amount comprising the employee's contribution under paragraph (a) of this subsection and the employer's contribution to the Pension Fund Custodian specified by the Pension Fund Administrator of the employee.
>
> (6) An employer who fails to deduct or remit the contributions within the time stipulated in subsection (3)(b) … shall, in addition to making the remittance already due, be liable to a penalty to be stipulated by the Commission.
>
> (7) The penalty … shall not be less than 2 percent of the total contribution that remains unpaid for each month or part of each month the default continues and the amount of the penalty shall be recoverable as a debt owed to the employee's retirement savings account.

Status: `verified_primary` (S3 OCR, rendered-page spot-check). Distinct from the PAYE remittance rule (F-011): pension contributions are due **within 7 working days of pay day**; PAYE is due by the **10th of the following month**.

### F-017 Annual returns, relief claims, and the filing channel

NTAA 2025 s.34, verbatim:

> (1) Every taxable person shall, on or before the due date, submit a self-assessment tax return with the relevant tax authority in accordance with the relevant provisions of this Act.
> (2) A taxable person who has submitted a self-assessment return in the prescribed form for a reporting period is deemed to have made an assessment of the amount of tax payable, including a negative or nil amount, for the reporting period to which the return relates.
> (4) Where a taxable person has delivered a tax return … the relevant tax authority may: (a) accept the tax return without making an additional assessment; (b) accept the tax return and make additional assessment; or (c) reject the tax return and, to the best of its judgement, determine the amount of the tax due … and make an assessment accordingly.
> (5) Where the taxable person fails to declare the true and correct amount of income or tax payable in its self-assessed tax returns, the taxable person is liable to pay any outstanding tax from the due date of the returns.

Filing practice (S5, LIRS): annual returns are filed on the LIRS **e-Tax platform** (`www.etax.lirs.net`) using the duly completed Income Tax Form (**Tax Form A**) "for return of income and claims for reliefs and allowances", with supporting documents uploaded (the F-012 list). **Every employee must file an individual annual return regardless of income level or prior PAYE deductions** (S5; statutory duty in s.13(1), F-011). HNWI guidance confirms returns cover "income from all sources as well as any reliefs and allowances claimed."

Status: `verified_primary` for the self-assessment duty (cleaned NTAA text, s.34); `verified_secondary` for the operational channel and form (S5). Relief claims are made **through the annual return**, not through a separate month-by-month approval process.

### F-018 Refunds, credits, and reconciliation of overpaid tax

NTAA 2025 s.55, verbatim:

> (1) There shall be refunded to taxpayers, after an audit by the relevant tax authority, such overpayment or any excess of tax as is due.
> (2) The relevant tax authority may make such rules and conditions necessary to facilitate the refund …
> (3) Any tax refund due shall be made within 90 days of the decision of the relevant tax authority … with the option of a set-off against any tax liability of the taxpayer.
> (7) No claim for refund of tax under this section shall be allowed unless it is made in writing within six years after the end of the year of assessment to which it relates.

Credit principle: s.72 (tax clearance) — a person who produces evidence of tax suffered by deduction at source is entitled to credit for it, "provided that any balance of tax after credit has been given for the tax so deducted has been fully paid." S10 reg. 5, verbatim: "A deduction made from a payment shall not be — (a) regarded as a separate tax or an additional cost of the contract or transaction; or (b) included in the contract price, but treated as an advance or final tax of the supplier, as the case may be."

Practice (S5): withholding tax is "recognised as tax paid in advance … and can be set off against assessed tax liability while the taxpayer remits the tax differential. Where the total WHT credit exceeds the tax due, the excess may either be applied as a credit against future tax liabilities or refunded … subject to submission of supporting documentation." On audit overpayments, LIRS "acknowledges the excess and informs the company while providing guidance on the process for a refund or application of the excess as a tax credit against future tax liability."

s.121, verbatim: "A person that receives a refund under section 55 of this Act, through a false or fictitious claim, is in addition to the recovery of the amount so received, liable to a penalty of 50% of that amount, plus interest at the prevailing Central Bank of Nigeria Monetary Policy Rate."

**Timing interpretation (answers "approval month vs backdated"):** the tax is an annual liability (F-002/F-001); PAYE is the monthly instalment collection (F-011); reliefs are claimed in the annual return and reduce the year's assessed liability (F-017). The difference between PAYE deducted and the corrected annual liability is settled by additional payment, set-off, credit, or refund under s.55 — i.e., the relief's benefit attaches to the **year of assessment**, and any over-deduction is recovered through the refund/credit mechanism, not through a retroactive re-run of past monthly PAYE.

Status: `verified_primary` (cleaned NTAA text, s.55/s.72); `verified_secondary` for practice (S5).

### F-019 Assessments, objections, and additional assessments

NTAA 2025, verbatim:

- **s.35(1):** "Where a taxable person has not delivered a tax return … the relevant tax authority … may, to the best of its judgement, determine the amount of the tax due … and make an assessment accordingly." (S5 calls this a Best of Judgment assessment.)
- **s.36(1):** "Where the relevant tax authority discovers or is of the opinion, at any time, that any taxable person liable to tax has not been assessed or has been assessed at an amount less than that which ought to have been charged, the relevant tax authority may, within six years of an assessment, assess the taxable person at such amount or additional amount, as ought to have been charged." (s.36(2): audit commenced within the period may continue; s.36(3): notice, appeal and other proceedings apply.)
- **s.41(1)–(2):** a taxable person disputing an assessment may "by a written notice of objection delivered in person, by courier service or via electronic means, apply … for the revision and amendment of the assessment"; the application is valid only if delivered **within 30 days from the date of service of the disputed notice of assessment** and contains the grounds of objection (specific issues with monetary values, amendments required, justification).

Status: `verified_primary` (cleaned NTAA text, s.35/36/41); corroborated by S5 (BOJ language; 30-day written objection).

## Pending facts (must be verified before use)

| ID | Fact needed | Source to verify | Why it matters |
|---|---|---|---|
| P-007 | NHF contribution rate and basis (commonly cited as 2.5% of monthly income) | NHF Act 1992, s.4 (as amended); Federal Mortgage Bank of Nigeria / NECA publications | Coach advice on NHF deductions and the size of the resulting deduction |
| P-008 | NHIS contribution rates and basis under the current scheme | National Health Insurance Authority Act 2022; NHIA guidelines | Coach advice on NHIS deductions and the size of the resulting deduction |

Not needed for the current prose (which states contributions are deductible without rates).

### Resolved

| Former ID | Resolution |
|---|---|
| P-001 Pension rates + VPCs | Promoted to **F-014** (rates, VPC basis and 5-year tax rule, quoted from the OCR'd PRA text; procedure via S8) and **F-016** (remittance within 7 working days, penalty ≥2%/month). |
| P-002 Minimum wage amount | Promoted to **F-015** — N70,000/month per S9 (bill text, enacted 2024), corroborated by S7. |
| P-003 PAYE administration | Promoted to **F-011**, verified_primary against NTAA 2025 (S6) — full gazette downloaded from the LIRS tax-legislation page |
| P-004 Rent relief evidence | Promoted to **F-012** (S5, regulator evidence requirements) |
| P-005 Mortgage interest evidence | Covered by **F-012** (same evidence-mandatory principle for all s.30(2)(a) reliefs) |
| P-006 PAYE remittance day | Resolved to **PAYE = 10th of the following month** (S5 LIRS regulator; corroborated by **S10**, the PwC analysis of the Deduction at Source (Withholding) Regulations 2024). NTAA s.107(1)'s 21st-day trigger is the general deduction-at-source framework; 2024 WHT timelines are 21st (FIRS) / 30th (state). See F-011. |

### Research notes (2026-09-19)

- **P-001/P-002 resolution (second pass):** user-side research supplied working URLs; `nigeriaopendata.com` statute-register pages + PenCom's guidelines index respond to **curl with a browser UA** even where the webfetch tool reports transport errors. From there: PenCom's *Guidelines on Voluntary Contribution* (S8) and the PLAC *National Minimum Wage (Amendment) Bill 2024* (S9) both extract cleanly with pypdf.
- **PRA 2014 (S3) encoding problem solved (OCR):** the PenCom PDF is a JBIG2 page scan with an invisible (`3 Tr`) scrambled text layer — extraction returns substituted codes, but the rendered glyphs are correct. `scripts/ocr_pra_2014.py` (PyMuPDF render at 200 dpi + RapidOCR) produced `sources/pra_2014_ocr.txt`, 62 pages / 136,401 chars, ~15 min. Spot-checks: s.4 (page 8) and s.10–11 (page 11) verified line-by-line against the rendered scan. OCR carries minor artifacts (e.g. "coitribution") — quote only spot-checked passages; do not add the raw OCR to the DAPT corpus.
- **PAYE deadline closed at primary level:** the gazetted Deduction of Tax at Source (Withholding) Regulations 2024 (S10; S.I. 34, Gazette No. 168, 2 Oct 2024) was obtained via a user-supplied mirror (`capacityhub.org`) — FIRS's site remains unreachable from here. Reg. 7(1): FIRS 21st, state CGT+PAYE 10th, state other deductions 30th. PwC's analysis (S11) cross-checks. Scribd link not needed.
- **Filing-mechanics pass (same day):** full LIRS FAQ downloaded (S5, 120K chars) → F-017 (e-Tax/Tax Form A; annual return carries relief claims; employees must file regardless of PAYE), F-018 (s.55 refunds: audit, 90-day payment, 6-year written claim; WHT credit/set-off; s.72 credit principle), F-019 (s.35 BOJ, s.36 six-year additional assessments, s.41 30-day written objection). These answer the practical relief-timing workflow: benefits attach to the year of assessment and settle via assessment/refund, not month-by-month re-runs.
- **Breakthrough:** the LIRS Tax Legislation page (`lirs.gov.ng/tax-information/tax-legislation`) hosts gazette PDFs for both the NTA 2025 and NTAA 2025 — both now downloaded and cleaned into the corpus.
- **Sources that failed:** SSA country profile (403), Bing search (garbage results via fetcher), DuckDuckGo (blocked), NigeriaLII legislation (empty database), PLAC lawsofnigeria (2004 laws only).

## Open items

- Pending facts (P-007, P-008) must not enter the corpus or training data until verified and promoted to the F-series. New facts enter only through this register.
- PRA 2014 now readable via OCR (S3) — spot-check any passage before quoting it; a retyped text is still preferable for corpus use.
- Nothing outstanding on the deduction-at-source timeline: the 2024 Regulations gazette is on file (S10) and quoted verbatim where needed.
- Lagos-specific procedural details captured via S5/S6/F-017–F-019; extend from LIRS pages as needed for coach behavior.
