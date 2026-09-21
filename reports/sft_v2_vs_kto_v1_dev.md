# Stage Comparison Report

- **before:** `data/captures/sft_v2_dev.jsonl` (30 records)
- **after:** `data/captures/kto_v1_dev.jsonl` (30 records)

## Summary

| Metric | Before | After |
|---|---|---|
| calculations scored | 9 | 9 |
| tax exact | 5 | 6 |
| tax within NGN 1 | 5 | 6 |
| chargeable income exact | 6 | 7 |
| chargeable income scored | 9 | 9 |
| savings exact | 0 | 0 |
| savings scored | 0 | 0 |

| Rate | Before | After |
|---|---|---|
| tax exact | 5/9 = 56% | 6/9 = 67% |
| tax within NGN 1 | 5/9 = 56% | 6/9 = 67% |
| chargeable income | 6/9 = 67% | 7/9 = 78% |
| savings exact | n/a | n/a |

## Paraphrase consistency (same predicted tax across 5 phrasings)

- before: 0/0 groups consistent
- after: 0/0 groups consistent

## Movement

- improved (tax wrong -> right): 2
- regressed (tax right -> wrong): 1
  - improved: base-en-04, base-pcm-04
  - regressed: base-pcm-05

## Per-prompt detail

### base-en-01

**Prompt:** What are the individual income-tax bands in Nigeria for the 2026 year of assessment?

**Before:** Here are the bands for the 2026 year of assessment: chargeable income up to NGN 800,000 is taxed at 0%; the next NGN 2,200,000 (NGN 800,000 to NGN 3,000,000) at 15%; the next NGN 9,000,000 (NGN 3,000,000 to NGN 12,000,000) at 18%; the next NGN 13,000,000 (NGN 12,000,000 to NGN 25,000,000) at 21%; the next NGN 25,000,000 (NGN 25,000,000 to NGN 50,000,000) at 23%; and anything above NGN 50,000,000 at 25%. The first NGN 800,000 is therefore tax-free.

**After:** Here are the bands for the 2026 year of assessment:  - Chargeable income up to NGN 800,000: no tax. - Chargeable income between NGN 800,000 and NGN 2,000,000: 15%. - Chargeable income between NGN 2,000,000 and NGN 5,000,000: 18%. - Chargeable income between NGN 5,000,000 and NGN 10,000,000: 21%. - Chargeable income between NGN 10,000,000 and NGN 25,000,000: 23%. - Chargeable income above NGN 25,000,000: 25%.

### base-en-02

**Prompt:** How is rent relief calculated under Nigeria's 2026 tax rules?

**Before:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be declared and evidence may be required.

**After:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be declared and evidence may be required.

### base-en-03

**Prompt:** I earn NGN 800,000 a year and no deductions or reliefs. How much tax do I pay? Please show the calculation.
**Expected tax:** 0.00 | before: 0.00 | after: 0.00

**Before:** Gross income: NGN 800,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 800,000. Band breakdown: first NGN 800,000 at 0% = NGN 0. Total tax: NGN 0.

**After:** Gross income: NGN 800,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 800,000. Band breakdown: first NGN 800,000 at 0% = NGN 0. Total tax: NGN 0.

### base-en-04

**Prompt:** I earn NGN 4,800,000 a year and I pay NGN 2,500,000 in rent. How much tax do I pay? Please show the calculation.
**Expected tax:** 564000.00 | before: 225000.00 | after: 564000.00

**Before:** Gross income: NGN 4,800,000. Reliefs applied: rent NGN 2,500,000 - total relief NGN 2,500,000. Chargeable income: NGN 2,300,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,500,000 at 15% = NGN 225,000. Total tax: NGN 225,000.

**After:** Gross income: NGN 4,800,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 4,300,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 1,300,000 at 18% = NGN 234,000. Total tax: NGN 564,000.

### base-en-05

**Prompt:** I earn NGN 250,000 every month and no deductions or reliefs. How much tax do I pay? Please show the calculation.
**Expected tax:** 330000.00 | before: 330000.00 | after: 330000.00

**Before:** Gross income: NGN 3,000,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 3,000,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000. Total tax: NGN 330,000.

**After:** Gross income: NGN 3,000,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 3,000,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000. Total tax: NGN 330,000.

### base-en-06

**Prompt:** I earn 3.6m a year and pay 800k rent. What's my tax?
**Expected tax:** 409200.00 | before: 409200.00 | after: 409200.00

**Before:** Gross income: NGN 3,600,000. Reliefs applied: rent (capped) NGN 160,000 - total relief NGN 160,000. Chargeable income: NGN 3,440,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 440,000 at 18% = NGN 79,200. Total tax: NGN 409,200.

**After:** Gross income: NGN 3,600,000. Reliefs applied: rent (capped) NGN 160,000 - total relief NGN 160,000. Chargeable income: NGN 3,440,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 440,000 at 18% = NGN 79,200. Total tax: NGN 409,200.

### base-en-07

**Prompt:** Using the Nigeria Tax Act 2025 guidelines, calculate the net monthly income for a salaried employee earning 500,000 NGN per month, assuming standard rent-relief deductions and the latest tax band adjustments.

**Before:** Gross income: NGN 6,000,000. Reliefs applied: rent NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 5,500,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,500,000 at 18% = NGN 450,000. Total tax: NGN 780,000.

**After:** Gross income: NGN 6,000,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 5,500,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,500,000 at 18% = NGN 450,000. Total tax: NGN 780,000.

### base-en-08

**Prompt:** I earn NGN 3,000,000 a year and no deductions or reliefs. How much tax do I pay? Please show the calculation.
**Expected tax:** 330000.00 | before: 330000.00 | after: 330000.00

**Before:** Gross income: NGN 3,000,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 3,000,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000. Total tax: NGN 330,000.

**After:** Gross income: NGN 3,000,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 3,000,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000. Total tax: NGN 330,000.

### base-en-09

**Prompt:** I earn NGN 50,000,001 a year and no deductions or reliefs. How much tax do I pay?
**Expected tax:** 10430000.25 | before: 932000.00 | after: 11780000.00

**Before:** Gross income: NGN 50,000,001. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 50,000,001. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 8,000,000 at 18% = NGN 1,440,000; next NGN 2,200,000 at 21% = NGN 462,000. Total tax: NGN 932,000.

**After:** Gross income: NGN 50,000,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 50,000,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 23,000,000 at 21% = NGN 4,830,000; next NGN 20,000,000 at 23% = NGN 4,600,000. Total tax: NGN 11,780,000.

### base-en-10

**Prompt:** I earn NGN 12,000,000 a year and I contribute NGN 240,000 to pension. What if I increase it to 480,000? How would my tax change?

**Before:** Your tax drops from NGN 1,968,000 to NGN 1,944,000. The extra NGN 120,000 comes off income taxed at 18%, and the pension relief lowers your chargeable income to NGN 11,640,000.

**After:** Your tax drops from NGN 1,926,400 to NGN 1,904,800. The extra NGN 120,000 comes off income taxed at 15%, lowering your chargeable income to NGN 11,680,000.

### base-en-11

**Prompt:** I earn NGN 300,000. Calculate my tax.

**Before:** Gross income: NGN 300,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 300,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 220,000 at 15% = NGN 33,000. Total tax: NGN 33,000.

**After:** Gross income: NGN 300,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 300,000. Band breakdown: first NGN 300,000 at 0% = NGN 0. Total tax: NGN 0.

### base-en-12

**Prompt:** I pay rent. Can I claim rent relief?

**Before:** Yes - rent relief is optional and you still declare it in your annual return.

**After:** Yes - rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. You must declare the actual rent correctly, and evidence may be required.

### base-en-13

**Prompt:** Is NHF contribution voluntary for private-sector employees?

**Before:** Yes - under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, the contribution is optional and deducted from emoluments.

**After:** Yes - under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, the contribution is optional and deducted from emoluments.

### base-en-14

**Prompt:** Can I deduct health insurance contributions?

**Before:** Yes - life, life assurance, NHIS and NHF contributions are deductible. The actual amount is claimed with evidence.

**After:** Yes - life, life assurance, NHIS and NHF contributions are deductible. You must declare them on your annual return.

### base-en-15

**Prompt:** I pay mortgage interest. How does that affect my tax?

**Before:** Mortgage interest is a qualifying deduction and is claimed on your annual return. It reduces your chargeable income, but the relief is capped at one-third of the total mortgage interest paid, and it is claimed only if the interest is actually paid.

**After:** Mortgage interest is a qualifying deduction and is claimed on your annual return. It reduces your chargeable income, but the relief is capped at one-third of the total mortgage interest paid, and it is claimed only if the interest is actually paid.

### base-en-16

**Prompt:** How much pension contribution can I deduct?

**Before:** Voluntary pension contribution: NGN 500,000 - no more, no less. Notify your employer in writing.

**After:** Your pension contribution is deductible and the amount is equal to one-third of your monthly emoluments, capped at 10% of your annual contribution, whichever is lower. You notify your employer in writing of the intention and the amount.

### base-en-17

**Prompt:** Can the tax authority ask for proof of my deduction claims?

**Before:** Yes. Section 31 of the Nigeria Tax Administration Act 2025 requires the tax authority to demand documentary evidence of the claim, and it may refuse the deduction or reduce the amount in the case of a false or fictitious claim. The evidence required is the claim form, and the authority may require it to be supported by evidence in the prescribed form.

**After:** Yes. The tax authority may demand documentary evidence of the claim in writing, and it may refuse the deduction, or part of it, where the evidence is absent or inadequate.

### base-en-18

**Prompt:** Calculate my Nigerian tax under the 2025 rules.

**Before:** I don't have access to your salary or reliefs - can you share them?

**After:** I don't have access to your salary or reliefs, so I can't calculate your tax. Could you share your salary and any reliefs you claim - pension, NHF, NHIS, life insurance, mortgage interest - and I'll work out your tax.

### base-en-19

**Prompt:** Calculate my Ghana personal income tax for 2026.

**Before:** I can't calculate personal income tax for Ghana - I only cover Nigerian personal income tax. Give me your salary and reliefs and I'll work out your tax.

**After:** I can't calculate your Ghana personal income tax - I only cover Nigerian personal income tax. If you share your salary and reliefs, I'll work out your chargeable income and tax.

### base-en-20

**Prompt:** Explain the step-by-step logic to compute a corporate employer's PAYE (Pay As You Earn) remittance obligations for a medium-sized enterprise under the 2026 tax framework.

**Before:** Here is the step-by-step logic to compute a corporate employer's PAYE remittance obligations for a medium-sized enterprise under the 2026 tax framework:  1. Identify the employees: list all employees, their monthly salaries, and the deductions to be applied. 2. Apply the tax table: calculate the tax using the 2026 tax table, which applies a consolidated band breakdown with a 15% minimum tax rate. 3. Demultiply by the monthly contribution: the monthly contribution is 10% of the tax computed, and the employer remits it to the state tax authority. 4. File the annual return: the employer files a t

**After:** Here is the step-by-step logic to compute a corporate employer's PAYE remittance obligations for a medium-sized enterprise under the 2026 tax framework:  1. **Determine the total monthly chargeable income.** The total monthly chargeable income is the employee's monthly contributions to the Pension Reform Act plus the employer's contribution, less eligible deductions such as rent, life insurance, and mortgage interest. 2. **Apply the marginal tax rates to the total chargeable income.** The first N800,000, the next NGN 2,200,000, the next NGN 9,000,000, the next NGN 23,000,000, the next NGN 46,0

### base-pcm-01

**Prompt:** Which individual income-tax bands dey for Nigeria for the 2026 year of assessment?

**Before:** Chargeable income up to NGN 800,000 dey at 0%. The next NGN 2,200,000 (NGN 800,000 go NGN 3,000,000) dey at 15%; the next NGN 9,000,000 (NGN 3,000,000 go NGN 12,000,000) at 18%; the next NGN 13,000,000 (NGN 12,000,000 go NGN 25,000,000) at 21%; the next NGN 25,000,000 (NGN 25,000,000 go NGN 50,000,000) at 23%; and anything above NGN 50,000,000 at 25%.

**After:** Chargeable income up to 800,000 dey taxed at 0%; the next 2,200,000 (800,000 to 3,000,000) dey taxed at 15%; the next 9,000,000 (3,000,000 to 12,000,000) dey taxed at 18%; the next 13,000,000 (12,000,000 to 25,000,000) dey taxed at 21%; the next 25,000,000 (25,000,000 to 50,000,000) dey taxed at 23%; and anything above 50,000,000 dey taxed at 25%. The first 800,000 dey no taxed.

### base-pcm-02

**Prompt:** How dem dey calculate rent relief for Nigeria 2026 tax?

**Before:** Rent relief na 20% of the annual rent wey dem pay, but e no fit pass NGN 500,000 - whichever one lower. Dem still dey claim the actual rent, with evidence.

**After:** Rent relief na 20% of the annual rent wey you pay, but e no fit pass NGN 500,000 - whichever one lower. You must declare the correct rent, and dem don deduct it from your chargeable income.

### base-pcm-03

**Prompt:** I dey earn 100k every month and I no get any deductions or reliefs. How much tax I go pay?
**Expected tax:** 60000.00 | before: None | after: None

**Before:** Is that 100,000 per month or 1,200,000 annually?

**After:** Is that 100,000 per month or 1,200,000 a year?

### base-pcm-04

**Prompt:** I dey earn 900k a year and I dey pay 1.2m for rent. How much tax I go pay?
**Expected tax:** 0.00 | before: 30000.00 | after: 0.00

**Before:** Gross income na NGN 900,000. Relief wey dey apply: rent NGN 1,200,000 - total relief na NGN 1,200,000. Chargeable income: NGN 0. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 200,000 at 15% = NGN 30,000. Total tax na NGN 30,000.

**After:** Gross income na NGN 900,000. Relief wey dey apply: rent (capped) NGN 240,000 - total relief na NGN 240,000. Chargeable income: NGN 660,000. Band breakdown: first NGN 660,000 at 0% = NGN 0. Total tax na NGN 0.

### base-pcm-05

**Prompt:** I dey earn 25m a year and I dey contribute 240k to pension. How much tax I go pay?
**Expected tax:** 4629600.00 | before: 4629600.00 | after: 5264800.00

**Before:** Gross income na NGN 25,000,000. Relief wey dey apply: pension NGN 240,000 - total relief na NGN 240,000. Chargeable income: NGN 24,760,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 12,760,000 at 21% = NGN 2,679,600. Total tax na NGN 4,629,600.

**After:** Gross income na NGN 25,000,000. Relief wey dey apply: pension NGN 240,000 - total relief na NGN 240,000. Chargeable income: NGN 24,760,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 12,000,000 at 21% = NGN 2,520,000; next NGN 4,760,000 at 23% = NGN 1,094,800. Total tax na NGN 5,264,800.

### base-pcm-06

**Prompt:** Wetin be the income tax bands for 2026?

**Before:** For 2026, the first NGN 800,000 na no dey inside the first band; the next NGN 2,200,000 (NGN 800,000 go NGN 3,000,000) dey inside the second band at 15%; the next NGN 9,000,000 (NGN 3,000,000 go NGN 12,000,000) dey inside the third band at 18%; the next NGN 13,000,000 (NGN 12,000,000 go NGN 25,000,000) dey inside the fourth band at 21%; the next NGN 25,000,000 (NGN 25,000,000 go NGN 50,000,000) dey inside the fifth band at 23%; and anything wey pass NGN 50,000,000 dey inside the sixth band at 25%.

**After:** For 2026, the first NGN 800,000 na no dey inside the first band; the next NGN 2,200,000 (NGN 800,000 go NGN 3,000,000) dey inside the second band at 15%; the next NGN 9,000,000 (NGN 3,000,000 go NGN 12,000,000) dey inside the third band at 18%; the next NGN 13,000,000 (NGN 12,000,000 go NGN 25,000,000) dey inside the fourth band at 21%; the next NGN 25,000,000 (NGN 25,000,000 go NGN 50,000,000) dey inside the fifth band at 23%; and anything wey pass NGN 50,000,000 dey inside the sixth band at 25%.

### base-pcm-07

**Prompt:** I no mention country or tax year. Wetin you go assume?

**Before:** If no country or tax year mention, I dey assume personal income tax for Nigeria, for the 2026 year of assessment.

**After:** If no country or tax year mention, I dey assume personal income tax for Nigeria, for the 2026 year of assessment.

### base-pcm-08

**Prompt:** Calculate my Ghana personal income tax for 2026.

**Before:** I can't calculate personal income tax for Ghana - I only cover Nigerian personal income tax. Give me your salary and reliefs and I'll work out your tax.

**After:** I can't calculate your Ghana personal income tax - I only cover Nigerian personal income tax. If you share your salary and reliefs, I'll work out your chargeable income and tax.

### base-pcm-09

**Prompt:** I dey earn NGN 300,000. Calculate my tax.

**Before:** Gross income na NGN 300,000. Relief wey dey apply: none - total relief na NGN 0. Chargeable income: NGN 300,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 220,000 at 15% = NGN 33,000. Total tax na NGN 33,000.

**After:** Gross income: NGN 300,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 300,000. Band breakdown: first NGN 300,000 at 0% = NGN 0. Total tax: NGN 0.

### base-pcm-10

**Prompt:** NHF contribution dey voluntary for private-sector workers?

**Before:** Yes - under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, a voluntary contribution scheme dey exist for private-sector workers, and individuals dey contribute am in excess of one-third of the month's salary.

**After:** Yes - under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, a voluntary contribution scheme dey exist for private-sector workers, and individuals dey contribute am in excess of one-third of their month's salary.
