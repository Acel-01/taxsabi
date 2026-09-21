# Stage Comparison Report

- **before:** `data/captures/sft_v2_coach.jsonl` (15 records)
- **after:** `data/captures/kto_v1_coach.jsonl` (15 records)

## Summary

| Metric | Before | After |
|---|---|---|
| calculations scored | 4 | 4 |
| tax exact | 0 | 0 |
| tax within NGN 1 | 0 | 0 |
| chargeable income exact | 0 | 0 |
| chargeable income scored | 4 | 4 |
| savings exact | 0 | 0 |
| savings scored | 3 | 3 |

| Rate | Before | After |
|---|---|---|
| tax exact | 0/4 = 0% | 0/4 = 0% |
| tax within NGN 1 | 0/4 = 0% | 0/4 = 0% |
| chargeable income | 0/4 = 0% | 0/4 = 0% |
| savings exact | 0/3 = 0% | 0/3 = 0% |

## Paraphrase consistency (same predicted tax across 5 phrasings)

- before: 0/0 groups consistent
- after: 0/0 groups consistent

## Movement

- improved (tax wrong -> right): 0
- regressed (tax right -> wrong): 0

## Per-prompt detail

### coach-01

**Prompt:** I'm a salaried employee on NGN 6,000,000 a year. I rent my flat and I've never claimed anything. What am I missing?

**Before:** Voluntary pension first - you can contribute 10% of your month's salary, and you can increase it to 15% by agreement with your employer. Then check your reliefs: rent, NHF, NHIS, life insurance, and a mortgage on a home you live in.

**After:** Let's find out. Do you pay rent, and do you contribute to pension, NHF, NHIS, and a life insurance policy?

### coach-02

**Prompt:** My salary is NGN 9,600,000 a year. I'm considering putting NGN 480,000 into voluntary pension this year. How much tax would that save me?
**Expected tax:** 1431600.00 | before: None | after: None

**Before:** Your tax drops from NGN 1,627,200 to NGN 1,605,600, because that NGN 480,000 comes off income taxed at 18%. Saving: NGN 21,600.

**After:** Your tax drops from NGN 1,624,800 to NGN 1,602,000, because that NGN 480,000 comes off income taxed at 18%. Saving: NGN 22,800.

### coach-03

**Prompt:** I earn NGN 7,200,000 a year and pay NGN 3,000,000 rent. If I claim the rent relief, how much tax does it save me?
**Expected tax:** 996000.00 | before: None | after: None

**Before:** Your tax drops from NGN 1,062,000 to NGN 1,034,400, because the extra NGN 3,000,000 comes off income that stays untaxed. Saving: NGN 27,600.

**After:** Your tax drops from NGN 1,062,000 to NGN 1,034,400, because the extra NGN 200,000 comes off income that stays untaxed. Saving: NGN 27,600.

### coach-04

**Prompt:** I earn NGN 13,000,000 a year. A friend said every NGN 100,000 of relief is worth NGN 25,000 to me. Is that right?
**Expected tax:** 2139000.00 | before: None | after: None

**Before:** No. Every NGN 100,000 of qualifying relief is worth NGN 50,000 to your tax, not NGN 25,000. The relief is a percentage of your chargeable income, and the higher the percentage, the larger the saving.

**After:** No. Every NGN 100,000 of eligible relief is worth NGN 50,000 to your tax, not NGN 25,000. The relief is a percentage of your chargeable income, and the higher the percentage, the larger the saving.

### coach-05

**Prompt:** I have about NGN 600,000 of spare savings this year, earning NGN 13,000,000. Should I put it into voluntary pension or something else?

**Before:** Voluntary pension is the way to go - it is deductible and you control the amount. Make sure you declare it properly and keep evidence of the contributions.

**After:** Voluntary pension is the way to go - it is deductible and you control the amount. Make sure you declare it properly and keep evidence of the contributions.

### coach-06

**Prompt:** My employer deducts PAYE monthly. I just paid two years of rent and I will file the relief claim next month. Will the relief apply from the month it is approved, or is it backdated?

**Before:** Relief approved by the relevant tax authority is paid no later than the 10th day of the month following the month in which it was claimed.

**After:** Relief approved by the relevant tax authority is paid no later than the 10th day of the month following the month in which it was claimed.

### coach-07

**Prompt:** Where do I actually submit a rent relief claim, and what do I upload with it?

**Before:** You upload a rent relief claim through your annual return: the claim must be written in the prescribed form (Tax Form A) and supported by evidence such as a lease agreement and a payslip.

**After:** You claim rent relief on your annual return: the claim is written in the prescribed form (Tax Form A) and supported by evidence such as a copy of your rent payment receipts.

### coach-08

**Prompt:** If the PAYE my employer deducted this year turns out to be more than my final tax after reliefs, what happens to the difference?

**Before:** The excess amount is refunded after an audit by the relevant tax authority, or claimed for a refund; it is not set off against other taxes.

**After:** The over-deduction is remitted to the relevant state tax authority, and the tax authority may allow a refund after an audit by itself.

### coach-09

**Prompt:** What documents do I need to keep for a rent relief claim?

**Before:** For a rent relief claim, you must keep evidence of rent paid: a rent receipt or a bank statement showing the actual rent paid.

**After:** For a rent relief claim, you must keep evidence of rent paid: a rent receipt or a bank statement showing the actual rent paid.

### coach-10

**Prompt:** How do I start a voluntary pension contribution, step by step?

**Before:** To start a voluntary pension contribution, follow these steps:  1. Decide the monthly amount: no more than one-third of your month's salary, and no less than 10% of your month's salary. 2. Notify your employer in writing of your intention and the amount. 3. Your employer remits the contribution to your RSA through your PFA once a month.

**After:** To start a voluntary pension contribution, follow these steps:  1. Decide the monthly amount: no more than one-third of your month's salary, and no less than 10% of your month's salary. 2. Notify your employer in writing of your intention and the amount. 3. Your employer remits the contribution to your RSA through your PFA once a month.

### coach-11

**Prompt:** I just discovered my employer has been keeping pension deductions for weeks before remitting. What are the rules and penalties?

**Before:** Under section 30 of the Nigeria Tax Act 2025, your employer must remit PAYE to the relevant state tax authority by the 10th day of the month following the month in which it was deducted. The employer is also liable to pay interest on the outstanding amount, with the rate determined by the Commission on Payment of Taxes (CPT) and payable on demand.

**After:** Under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, your employer must remit the monthly pension contribution to your retirement account by the 10th day of the month following the month in which it was made. The employer is also liable to pay a penalty for any late remittance, with the amount being 2% of the total amount due for each month or part of a month the payment is late, capped at NGN 10,000.

### coach-12

**Prompt:** Work out my tax: salary NGN 8,400,000 a year, pension contributions NGN 500,000, rent NGN 2,400,000 a year, NHIS NGN 72,000 and NHF NGN 60,000.
**Expected tax:** 1101840.00 | before: 1141440.00 | after: 1159440.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, rent NGN 2,400,000, NHIS NGN 72,000, NHF NGN 60,000 - total relief NGN 892,000. Chargeable income: NGN 7,508,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,508,000 at 18% = NGN 811,440. Total tax: NGN 1,141,440.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, rent NGN 2,400,000, NHIS NGN 72,000, NHF NGN 60,000 - total relief NGN 792,000. Chargeable income: NGN 7,608,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,608,000 at 18% = NGN 829,440. Total tax: NGN 1,159,440.

### coach-13

**Prompt:** I earn the national minimum wage. My friend says I should still file tax and claim reliefs even though I pay no tax. Is that right?

**Before:** Yes, that is right. Even if PAYE deducted leaves no tax, you still file an annual return and can claim reliefs such as pension, NHF, NHIS, life insurance, and mortgage interest.

**After:** Yes, that is right. Even if PAYE is already being deducted, you still file an annual return and can claim reliefs such as pension, life insurance, and NHF contributions.

### coach-14

**Prompt:** Can you help me compute the VAT my company must remit this month?

**Before:** I can't help with VAT remittance - I only cover personal income tax on salaries in Nigeria. Give me your salary and reliefs and I'll calculate your personal tax.

**After:** I can't help with VAT remittance - I only cover personal income tax. If you share your salary and reliefs, I'll calculate your personal tax.

### coach-15

**Prompt:** I'm getting a raise next month that takes me from NGN 9,600,000 to NGN 12,000,000 a year. How should I plan so the extra tax doesn't eat the whole increase?

**Before:** Understand that your tax drops from NGN 1,838,400 to NGN 1,764,000, because the extra NGN 2,400,000 comes off income taxed at 18%. Keep your salary at NGN 10,000,000 a year for the relief.

**After:** Understand that your tax drops from NGN 1,838,400 to NGN 1,764,000, because the extra NGN 2,400,000 comes off income taxed at 18%. Keep your salary at NGN 10,800,000 a year for the relief.
