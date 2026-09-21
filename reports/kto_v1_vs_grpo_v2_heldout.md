# Stage Comparison Report

- **before:** `data/captures/kto_v1_heldout.jsonl` (20 records)
- **after:** `data/captures/grpo_v2_probe_prompts_heldout.jsonl` (20 records)

## Summary

| Metric | Before | After |
|---|---|---|
| calculations scored | 10 | 10 |
| tax exact | 5 | 5 |
| tax within NGN 1 | 5 | 5 |
| chargeable income exact | 7 | 7 |
| chargeable income scored | 10 | 10 |
| savings exact | 0 | 0 |
| savings scored | 0 | 0 |

| Rate | Before | After |
|---|---|---|
| tax exact | 5/10 = 50% | 5/10 = 50% |
| tax within NGN 1 | 5/10 = 50% | 5/10 = 50% |
| chargeable income | 7/10 = 70% | 7/10 = 70% |
| savings exact | n/a | n/a |

## Paraphrase consistency (same predicted tax across 5 phrasings)

- before: 0/0 groups consistent
- after: 0/0 groups consistent

## Movement

- improved (tax wrong -> right): 0
- regressed (tax right -> wrong): 0

## Per-prompt detail

### probe-calc-01

**Prompt:** I earn NGN 1,450,000 a year and no deductions or reliefs. How much tax do I pay?
**Expected tax:** 97500.00 | before: 97500.00 | after: 97500.00

**Before:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

**After:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

### probe-calc-02

**Prompt:** I earn NGN 90,000 every month and no deductions. What's my annual tax?
**Expected tax:** 42000.00 | before: 42000.00 | after: 42000.00

**Before:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

**After:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

### probe-calc-03

**Prompt:** I earn NGN 5,750,000 a year and pay NGN 1,800,000 in rent. How much tax do I pay?
**Expected tax:** 760200.00 | before: 760200.00 | after: 760200.00

**Before:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

**After:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

### probe-calc-04

**Prompt:** I earn NGN 1,050,000 a year and contribute NGN 45,000 to pension. How much tax do I pay?
**Expected tax:** 30750.00 | before: 38250.00 | after: 38250.00

**Before:** Gross income: NGN 1,050,000. Reliefs applied: pension NGN 45,000 - total relief NGN 45,000. Chargeable income: NGN 1,005,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 255,000 at 15% = NGN 38,250. Total tax: NGN 38,250.

**After:** Gross income: NGN 1,050,000. Reliefs applied: pension NGN 45,000 - total relief NGN 45,000. Chargeable income: NGN 1,005,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 255,000 at 15% = NGN 38,250. Total tax: NGN 38,250.

### probe-calc-05

**Prompt:** What's my take-home pay if I earn NGN 2,100,000 a year with no deductions?
**Expected tax:** 195000.00 | before: 195000.00 | after: 195000.00

**Before:** Gross income: NGN 2,100,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 2,100,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,300,000 at 15% = NGN 195,000. Total tax: NGN 195,000.

**After:** Gross income: NGN 2,100,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 2,100,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,300,000 at 15% = NGN 195,000. Total tax: NGN 195,000.

### probe-calc-06

**Prompt:** I earn NGN 8,400,000 a year, contribute NGN 500,000 to pension and NGN 72,000 to NHIS. How much tax do I pay?
**Expected tax:** 1199040.00 | before: 1199040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### probe-calc-07

**Prompt:** I earn NGN 32,000,000 a year and pay NGN 900,000 in rent. How much tax do I pay?
**Expected tax:** 6248600.00 | before: 5920600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### probe-calc-08

**Prompt:** I dey earn 70k every month. How much tax I go pay?
**Expected tax:** 6000.00 | before: None | after: None

**Before:** Is that 70,000 per month or 700,000 annually?

**After:** Is that 70,000 per month or 700,000 annually?

### probe-calc-09

**Prompt:** My rent na 600k a year. How much relief I fit get?
**Expected tax:** 0.00 | before: None | after: 42000.00

**Before:** Is that 600,000 monthly or 600,000 annual? Relief na 0 - no rent payment at all, so nothing to reduce chargeable income.

**After:** Gross income na NGN 1,200,000. Relief wey dey apply: rent (capped) NGN 120,000 - total relief na NGN 120,000. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax na NGN 42,000.

### probe-calc-10

**Prompt:** I earn NGN 2,700,000 a year and I pay 450k for rent. How much tax I go pay?
**Expected tax:** 271500.00 | before: 210000.00 | after: 210000.00

**Before:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 2,200,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,400,000 at 15% = NGN 210,000. Total tax: NGN 210,000.

**After:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 2,200,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,400,000 at 15% = NGN 210,000. Total tax: NGN 210,000.

### probe-clar-01

**Prompt:** My salary is NGN 700,000. How much tax do I owe?

**Before:** Gross income: NGN 700,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 700,000. Band breakdown: first NGN 700,000 at 0% = NGN 0. Total tax: NGN 0.

**After:** Gross income: NGN 700,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 700,000. Band breakdown: first NGN 700,000 at 0% = NGN 0. Total tax: NGN 0.

### probe-clar-02

**Prompt:** I dey contribute to pension. How much tax I go save?

**Before:** Can you tell me your monthly income and how much you dey contribute to pension?

**After:** Can you tell me your monthly income and how much you dey contribute to pension?

### probe-fact-01

**Prompt:** How many tax bands apply to individuals in Nigeria in 2026, and what is each rate?

**Before:** In 2026, the Nigerian tax authority applies the Fourth Schedule tax table to individuals, with the following bands: chargeable income up to NGN 800,000 is taxed at 0%; the next NGN 2,200,000 (NGN 800,000 to NGN 3,000,000) at 15%; the next NGN 9,000,000 (NGN 3,000,000 to NGN 12,000,000) at 18%; the next NGN 13,000,000 (NGN 12,000,000 to NGN 25,000,000) at 21%; the next NGN 25,000,000 (NGN 25,000,000 to NGN 50,000,000) at 23%; and anything above NGN 50,000,000 at 25%.

**After:** In 2026, individuals are taxed on their chargeable income using the following bands: chargeable income up to NGN 800,000 is taxed at 0%; the next NGN 2,200,000 (NGN 800,000 to NGN 3,000,000) at 15%; the next NGN 9,000,000 (NGN 3,000,000 to NGN 12,000,000) at 18%; the next NGN 13,000,000 (NGN 12,000,000 to NGN 25,000,000) at 21%; the next NGN 25,000,000 (NGN 25,000,000 to NGN 50,000,000) at 23%; and anything above NGN 50,000,000 at 25%.

### probe-fact-02

**Prompt:** Is the rent deduction capped, and if so, at what amount?

**Before:** Yes - the rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** Yes - the rent relief is 20% of the annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### probe-fact-03

**Prompt:** Can I deduct my children's school fees from my taxable income?

**Before:** No - only rent paid on a home you live in can be deducted, and rent relief is capped at one-third of annual rent paid. Write a claim in your annual return.

**After:** No - only rent paid on a home you live in can be deducted, and rent relief is capped at one-third of annual rent paid. Write a claim in your annual return for the deduction.

### probe-fact-04

**Prompt:** Wetin be the difference between pension and NHF contribution for tax?

**Before:** Both pension and NHF contributions are deductible and can be claimed separately. The difference is that NHF contribution dey inside your RSA and you control the amount, while pension contribution dey through your employer and you dey notify your employer in writing.

**After:** The difference be simple: pension contribution wey you remit into your own RSA dem deduct from your salary, while NHF contribution wey you remit go the National Housing Fund for your own home. Both dem allow you to choose the amount, and you notify your employer in writing how much you intend to contribute.

### probe-fact-05

**Prompt:** The tax office need wetin as proof for my pension claim?

**Before:** For a pension relief claim, the claim must be made in writing in the prescribed form (Tax Form A) and supported by evidence of the amount, under section 30(2)(a) of the Nigeria Tax Act 2025. The evidence may include a payslip, a certificate of pension contribution, or a statement of pension.

**After:** For a pension relief claim, the claim must be made in writing in the prescribed form (Tax Form A) and supported by evidence of the amount, under section 30 of the Nigeria Tax Act 2025. The evidence may include a payslip, a certificate of pension contribution, or a statement of pension.

### probe-scope-01

**Prompt:** Do these personal income tax rules apply to a company director?

**Before:** No - the personal income tax rules apply only to individuals. A company director is taxed on their chargeable income, under the Nigeria Tax Act 2025, whether or not they are a member of the company.

**After:** No - the personal income tax rules apply only to individuals. A company director is an individual, so the director's personal income tax table applies to their chargeable income.

### probe-scope-02

**Prompt:** I'm a student with no income. Do I need to file tax?

**Before:** No - under the Fourth Schedule of the Nigeria Tax Act 2025, a person with chargeable income not exceeding NGN 800,000 is exempt from income tax on their chargeable income; and a person with no chargeable income is exempt from income tax on that income.

**After:** No - under the Fourth Schedule of the Nigeria Tax Act 2025, a person with chargeable income not exceeding NGN 800,000 is exempt from income tax on their chargeable income; and a person with no chargeable income is exempt from income tax on that income.

### probe-scope-03

**Prompt:** Abuja vs Lagos — any difference in tax?

**Before:** There is no difference in tax between the two cities. The tax treatment for individuals is the same throughout Nigeria, and the Lagos State and Federal governments have no authority over personal income tax except what is prescribed by the Nigeria Tax Act.

**After:** There is no difference in tax between the two cities. The tax treatment for individuals is the same throughout Nigeria, and the Lagos State and Federal governments have no authority over personal income tax.
