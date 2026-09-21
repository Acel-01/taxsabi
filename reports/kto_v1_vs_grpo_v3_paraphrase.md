# Stage Comparison Report

- **before:** `data/captures/kto_v1_paraphrase.jsonl` (100 records)
- **after:** `data/captures/grpo_v3_paraphrase_suite.jsonl` (100 records)

## Summary

| Metric | Before | After |
|---|---|---|
| calculations scored | 40 | 40 |
| tax exact | 17 | 17 |
| tax within NGN 1 | 17 | 17 |
| chargeable income exact | 22 | 22 |
| chargeable income scored | 40 | 40 |
| savings exact | 0 | 0 |
| savings scored | 10 | 10 |

| Rate | Before | After |
|---|---|---|
| tax exact | 17/40 = 42% | 17/40 = 42% |
| tax within NGN 1 | 17/40 = 42% | 17/40 = 42% |
| chargeable income | 22/40 = 55% | 22/40 = 55% |
| savings exact | 0/10 = 0% | 0/10 = 0% |

## Paraphrase consistency (same predicted tax across 5 phrasings)

- before: 3/8 groups consistent
- after: 6/8 groups consistent

Before inconsistencies: para-calc-01: ['124500.00', '97500.00']; para-calc-03: ['549600.00', '760200.00']; para-calc-04: ['1127040.00', '1199040.00']; para-calc-05: ['157500.00', '271500.00', '277500.00']; para-calc-08: ['5918600.00', '5920600.00']

After inconsistencies: para-calc-03: ['562200.00', '760200.00']; para-calc-05: ['158400.00', '210000.00', '277500.00']

## Movement

- improved (tax wrong -> right): 1
- regressed (tax right -> wrong): 1
  - improved: para-calc-04-e
  - regressed: para-calc-05-a

## Per-prompt detail

### para-calc-01-a

**Prompt:** I earn NGN 1,450,000 a year and no deductions or reliefs. How much tax do I pay?
**Expected tax:** 97500.00 | before: 97500.00 | after: 97500.00

**Before:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

**After:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

### para-calc-01-b

**Prompt:** So my yearly pay is 1.45m and I have no reliefs. What do I pay?
**Expected tax:** 97500.00 | before: None | after: None

**Before:** Voluntary pension first - it is deductible and you choose the amount.

**After:** Voluntary pension first - it is deductible and you choose the amount.

### para-calc-01-c

**Prompt:** 1.45m/yr, zero reliefs - tax?
**Expected tax:** 97500.00 | before: 97500.00 | after: 97500.00

**Before:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

**After:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

### para-calc-01-d

**Prompt:** I'm trying to plan my budget for next year. My gross annual salary will be NGN 1,450,000, I don't contribute to any scheme and I don't claim any reliefs. What would my income tax be?
**Expected tax:** 97500.00 | before: 97500.00 | after: 97500.00

**Before:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

**After:** Gross income: NGN 1,450,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,450,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500. Total tax: NGN 97,500.

### para-calc-01-e

**Prompt:** A colleague told me someone on a 1.45m annual salary with no reliefs pays nothing. Is that right, and what is the actual tax?
**Expected tax:** 97500.00 | before: 124500.00 | after: None

**Before:** Yes, that person pays nothing. After the zero band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 650,000 at 15% = NGN 97,500; next NGN 150,000 at 18% = NGN 27,000. Total tax: NGN 124,500.

**After:** Yes, that person pays nothing. After reliefs, chargeable income falls to 0: a salary of NGN 1,450,000 is within the tax-free band, and the excess is deducted.

### para-calc-02-a

**Prompt:** I earn NGN 90,000 every month with no deductions. What is my annual tax?
**Expected tax:** 42000.00 | before: 42000.00 | after: 42000.00

**Before:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

**After:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

### para-calc-02-b

**Prompt:** 90k enters my account every month, no deductions. How much tax for the whole year?
**Expected tax:** 42000.00 | before: 42000.00 | after: 42000.00

**Before:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

**After:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

### para-calc-02-c

**Prompt:** 90k/month. Annual tax?
**Expected tax:** 42000.00 | before: 42000.00 | after: 42000.00

**Before:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

**After:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

### para-calc-02-d

**Prompt:** I get paid NGN 90,000 at the end of every month and I have no deductions at all. Please work out my total tax for the year.
**Expected tax:** 42000.00 | before: 42000.00 | after: 42000.00

**Before:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

**After:** Gross income: NGN 1,080,000. Reliefs applied: none - total relief NGN 0. Chargeable income: NGN 1,080,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 280,000 at 15% = NGN 42,000. Total tax: NGN 42,000.

### para-calc-02-e

**Prompt:** Someone said a person earning 90,000 a month pays about 42,000 tax a year. Is that calculation correct?
**Expected tax:** 42000.00 | before: None | after: None

**Before:** No. A person earning NGN 900,000 a month (NGN 1,080,000 annually) pays NGN 106,440 in tax. The first NGN 800,000 is taxed at 0%, the next NGN 280,000 at 15%, and the remaining NGN 0 at 18%.

**After:** No - that is not correct. A person earning NGN 900,000 a month (NGN 1,080,000 annually) pays NGN 106,440 in tax. The first NGN 800,000 is taxed at 0%, the next NGN 280,000 at 15%, and the remaining NGN 0 at 18%.

### para-calc-03-a

**Prompt:** I earn NGN 5,750,000 a year and pay NGN 1,800,000 in rent. How much tax do I pay?
**Expected tax:** 760200.00 | before: 760200.00 | after: 760200.00

**Before:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

**After:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

### para-calc-03-b

**Prompt:** My salary is 5.75m for the year and my rent is 1.8m. What is my tax?
**Expected tax:** 760200.00 | before: 760200.00 | after: 760200.00

**Before:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

**After:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

### para-calc-03-c

**Prompt:** 5.75m/yr, rent 1.8m. Tax?
**Expected tax:** 760200.00 | before: 760200.00 | after: 760200.00

**Before:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

**After:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

### para-calc-03-d

**Prompt:** I'm gathering figures for my annual return. Gross salary of NGN 5,750,000 and annual rent of NGN 1,800,000. Can you compute my income tax after the rent relief?
**Expected tax:** 760200.00 | before: 760200.00 | after: 760200.00

**Before:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

**After:** Gross income: NGN 5,750,000. Reliefs applied: rent (capped) NGN 360,000 - total relief NGN 360,000. Chargeable income: NGN 5,390,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 2,390,000 at 18% = NGN 430,200. Total tax: NGN 760,200.

### para-calc-03-e

**Prompt:** My friend with a 5.75m salary and 1.8m rent says his tax comes to about 900k. Is that figure right?
**Expected tax:** 760200.00 | before: 549600.00 | after: 562200.00

**Before:** Let's check. Reliefs we apply: rent relief @ 20% of the rent, capped at NGN 500,000 - total relief NGN 130,000. Chargeable income: NGN 4,220,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 1,220,000 at 18% = NGN 219,600. Total tax: NGN 549,600.

**After:** Let's check. Reliefs we apply: rent relief @ 20% of the rent - NGN 360,000; total relief NGN 360,000. Chargeable income: NGN 4,290,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 1,290,000 at 18% = NGN 232,200. Total tax: NGN 562,200.

### para-calc-04-a

**Prompt:** I earn NGN 8,400,000 a year, contribute NGN 500,000 to pension and NGN 72,000 to NHIS. How much tax do I pay?
**Expected tax:** 1199040.00 | before: 1199040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### para-calc-04-b

**Prompt:** I earn 8.4m yearly. I contribute 500k to pension and 72k to NHIS. What will I pay?
**Expected tax:** 1199040.00 | before: 1199040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### para-calc-04-c

**Prompt:** 8.4m/yr + pension 500k + NHIS 72k. Tax?
**Expected tax:** 1199040.00 | before: 1199040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### para-calc-04-d

**Prompt:** Before I file, I want to be sure of the numbers: annual salary NGN 8,400,000, annual pension contributions NGN 500,000, NHIS contributions NGN 72,000. What is my chargeable income and tax?
**Expected tax:** 1199040.00 | before: 1199040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### para-calc-04-e

**Prompt:** I was told that with an 8.4m salary, 500k pension and 72k NHIS, my tax should be around 1.4m. Can you verify?
**Expected tax:** 1199040.00 | before: 1127040.00 | after: 1199040.00

**Before:** Gross income: NGN 8,000,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,428,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,428,000 at 18% = NGN 797,040. Total tax: NGN 1,127,040.

**After:** Gross income: NGN 8,400,000. Reliefs applied: pension NGN 500,000, NHIS NGN 72,000 - total relief NGN 572,000. Chargeable income: NGN 7,828,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 4,828,000 at 18% = NGN 869,040. Total tax: NGN 1,199,040.

### para-calc-05-a

**Prompt:** I earn NGN 2,700,000 a year and pay NGN 450,000 rent. How much tax do I pay?
**Expected tax:** 271500.00 | before: 271500.00 | after: 277500.00

**Before:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 90,000. Chargeable income: NGN 2,610,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,810,000 at 15% = NGN 271,500. Total tax: NGN 271,500.

**After:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 50,000. Chargeable income: NGN 2,650,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,850,000 at 15% = NGN 277,500. Total tax: NGN 277,500.

### para-calc-05-b

**Prompt:** My pay is 2.7m for the year and rent is 450k. How much tax?
**Expected tax:** 271500.00 | before: 277500.00 | after: 210000.00

**Before:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 50,000. Chargeable income: NGN 2,650,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,850,000 at 15% = NGN 277,500. Total tax: NGN 277,500.

**After:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 2,200,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,400,000 at 15% = NGN 210,000. Total tax: NGN 210,000.

### para-calc-05-c

**Prompt:** 2.7m/yr, rent 450k. Tax?
**Expected tax:** 271500.00 | before: 277500.00 | after: 210000.00

**Before:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 50,000. Chargeable income: NGN 2,650,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,850,000 at 15% = NGN 277,500. Total tax: NGN 277,500.

**After:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 500,000 - total relief NGN 500,000. Chargeable income: NGN 2,200,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,400,000 at 15% = NGN 210,000. Total tax: NGN 210,000.

### para-calc-05-d

**Prompt:** I am putting my tax records together: gross annual income NGN 2,700,000 and I paid NGN 450,000 as rent for the year. Please calculate my tax liability.
**Expected tax:** 271500.00 | before: 277500.00 | after: 277500.00

**Before:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 50,000. Chargeable income: NGN 2,650,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,850,000 at 15% = NGN 277,500. Total tax: NGN 277,500.

**After:** Gross income: NGN 2,700,000. Reliefs applied: rent (capped) NGN 50,000 - total relief NGN 50,000. Chargeable income: NGN 2,650,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 1,850,000 at 15% = NGN 277,500. Total tax: NGN 277,500.

### para-calc-05-e

**Prompt:** My brother says a 2.7m salary with 450k rent attracts tax of roughly 271,500. Is he correct?
**Expected tax:** 271500.00 | before: 157500.00 | after: 158400.00

**Before:** Let's check. Chargeable income: NGN 1,800,000. Total tax: NGN 157,500.

**After:** Let's check. Chargeable income: NGN 1,850,000. Total tax: NGN 158,400.

### para-calc-06-a

**Prompt:** I earn NGN 13,000,000 a year and make no contributions. If I contribute NGN 300,000 to voluntary pension this year, what will my tax be and how much will it save me?
**Expected tax:** 2097000.00 | before: None | after: None

**Before:** Your tax drops from NGN 2,073,600 to NGN 2,048,400. The contribution lowers your chargeable income to NGN 12,700,000. Saving: NGN 25,200.

**After:** Your tax drops from NGN 2,073,600 to NGN 2,048,400. The contribution lowers your chargeable income to NGN 12,700,000. Saving: NGN 25,200.

### para-calc-06-b

**Prompt:** 13m salary, nothing is deducted. If I add 300k voluntary pension, what will my tax be and how much will I save?
**Expected tax:** 2097000.00 | before: None | after: None

**Before:** Your tax drops from NGN 2,136,600 to NGN 2,106,000, because the extra NGN 300,000 comes off income taxed at 18%. Saving: NGN 30,600.

**After:** Your tax drops from NGN 2,130,000 to NGN 1,950,000, because the extra NGN 300,000 comes off income taxed at 18%. Saving: NGN 180,000.

### para-calc-06-c

**Prompt:** 13m/yr, add 300k VPC - new tax and savings?
**Expected tax:** 2097000.00 | before: None | after: None

**Before:** Your tax drops from NGN 2,130,000 to NGN 1,950,000, because the extra NGN 300,000 comes off income taxed at 15%. Keep your VPC deduction certificate for the claim. Saving: NGN 180,000.

**After:** Your tax drops from NGN 2,130,000 to NGN 1,950,000, because the extra NGN 300,000 comes off income taxed at 15%. Keep your VPC deduction certificate for the claim. Saving: NGN 180,000.

### para-calc-06-d

**Prompt:** I'm considering voluntary pension contributions as a year-end move. Annual income is NGN 13,000,000 with no other contributions; if I put NGN 300,000 into voluntary pension, what is my tax afterwards and the saving versus doing nothing?
**Expected tax:** 2097000.00 | before: None | after: None

**Before:** Your tax drops from NGN 2,220,000 to NGN 2,190,000. Doing nothing saves NGN 30,000, which is less than the amount you contribute, so the voluntary contribution is worthwhile.

**After:** Your tax drops from NGN 2,073,000 to NGN 2,045,000. The saving is NGN 28,000.

### para-calc-06-e

**Prompt:** An adviser told me a 300k voluntary pension on a 13m salary saves about 63k tax. Can you check that claim?
**Expected tax:** 2097000.00 | before: 120000.00 | after: 65550.00

**Before:** Let's check. Reliefs applied: voluntary pension 63,000 - total relief 63,000. Chargeable income: 1,237,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 430,000 at 15% = NGN 64,500; next NGN 307,000 at 18% = NGN 55,260. Total tax: NGN 120,000.

**After:** Let's check. Reliefs applied: voluntary pension 63,000 - total relief 63,000. Chargeable income: 1,237,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 437,000 at 15% = NGN 65,550. Total tax: NGN 65,550.

### para-calc-07-a

**Prompt:** I earn NGN 5,000,000 a year. I'm about to sign a NGN 2,400,000 annual rent. How much tax will I pay after the rent relief, and how much does the relief save me?
**Expected tax:** 603600.00 | before: None | after: None

**Before:** Your tax drops from NGN 670,000 to NGN 642,000. The rent relief you claim lowers your chargeable income to NGN 4,200,000. Saving: NGN 28,000.

**After:** Your tax drops from NGN 670,000 to NGN 648,000. The rent relief you claim lowers your chargeable income to NGN 4,600,000. Saving: NGN 22,000.

### para-calc-07-b

**Prompt:** My salary is 5m and I want to rent a place that costs 2.4m a year. After rent relief, what is my tax and how much does the relief save me?
**Expected tax:** 603600.00 | before: None | after: None

**Before:** Your tax drops from NGN 870,000 to NGN 690,000. The rent relief you claim lowers your chargeable income to NGN 4,200,000.

**After:** Your tax drops from NGN 870,000 to NGN 690,000. The rent relief you claim lowers your chargeable income to NGN 4,200,000. Saving: NGN 180,000.

### para-calc-07-c

**Prompt:** 5m/yr, rent 2.4m - tax and savings from relief?
**Expected tax:** 603600.00 | before: 603600.00 | after: 603600.00

**Before:** Gross income: NGN 5,000,000. Reliefs applied: rent (capped) NGN 480,000 - total relief NGN 480,000. Chargeable income: NGN 4,520,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 1,520,000 at 18% = NGN 273,600. Total tax: NGN 603,600. Keep your rent receipts and PAYE deducted from salary for the claim and the deduction.

**After:** Gross income: NGN 5,000,000. Reliefs applied: rent (capped) NGN 480,000 - total relief NGN 480,000. Chargeable income: NGN 4,520,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 1,520,000 at 18% = NGN 273,600. Total tax: NGN 603,600. Keep your rent receipts for the claim.

### para-calc-07-d

**Prompt:** I am comparing locations: annual income NGN 5,000,000, and one option means paying NGN 2,400,000 in rent for the year. With the rent relief applied, what would my tax be and what is the saving from the relief?
**Expected tax:** 603600.00 | before: None | after: None

**Before:** Your tax drops from NGN 570,000 to NGN 549,000. The rent relief you claim lowers your chargeable income to NGN 4,200,000. Saving: NGN 21,000.

**After:** Your tax drops from NGN 570,000 to NGN 549,000. The rent relief you claim lowers your chargeable income to NGN 4,200,000. Saving: NGN 21,000.

### para-calc-07-e

**Prompt:** Someone claims a 2.4m rent on a 5m salary cuts tax by about 86,400. Is that right, and what is the tax after the relief?
**Expected tax:** 603600.00 | before: None | after: None

**Before:** Yes, that is right. The tax drops from NGN 276,000 to NGN 189,600. The relief is the rent: 20% of the annual rent, capped at NGN 500,000.

**After:** Yes, that is right. The tax drops from NGN 174,000 to NGN 87,600. The relief comes because rent of NGN 480,000 is deducted from salary and the chargeable income falls to NGN 2,220,000.

### para-calc-08-a

**Prompt:** I earn NGN 32,000,000 a year and pay NGN 900,000 in rent. How much tax do I pay?
**Expected tax:** 6248600.00 | before: 5920600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### para-calc-08-b

**Prompt:** 32m salary for the year, rent 900k. What is my tax?
**Expected tax:** 6248600.00 | before: 5920600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### para-calc-08-c

**Prompt:** 32m/yr, rent 900k. Tax?
**Expected tax:** 6248600.00 | before: 5920600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### para-calc-08-d

**Prompt:** For my annual planning: gross income NGN 32,000,000, annual rent NGN 900,000. Please compute the chargeable income and total tax.
**Expected tax:** 6248600.00 | before: 5918600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,338,600. Total tax: NGN 5,918,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### para-calc-08-e

**Prompt:** I'm told tax on a 32m salary with 900k rent is over 6m. Can you confirm the exact figure?
**Expected tax:** 6248600.00 | before: 5920600.00 | after: 5920600.00

**Before:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

**After:** Gross income: NGN 32,000,000. Reliefs applied: rent (capped) NGN 180,000 - total relief NGN 180,000. Chargeable income: NGN 31,820,000. Band breakdown: first NGN 800,000 at 0% = NGN 0; next NGN 2,200,000 at 15% = NGN 330,000; next NGN 9,000,000 at 18% = NGN 1,620,000; next NGN 13,000,000 at 21% = NGN 2,730,000; next NGN 5,820,000 at 23% = NGN 1,340,600. Total tax: NGN 5,920,600.

### para-fact-01-a

**Prompt:** What are the individual income-tax bands and rates in Nigeria for the 2026 year of assessment?

**Before:** Here are the bands and rates for 2026:  - Chargeable income up to NGN 800,000: 0% - Chargeable income between NGN 800,000 and NGN 2,000,000: 15% - Chargeable income between NGN 2,000,000 and NGN 5,000,000: 18% - Chargeable income between NGN 5,000,000 and NGN 10,000,000: 21% - Chargeable income between NGN 10,000,000 and NGN 25,000,000: 23% - Chargeable income above NGN 25,000,000: 25%  The first NGN 800,000 is therefore tax-free.

**After:** Here are the bands and rates for the 2026 year of assessment:  - Chargeable income up to NGN 800,000: 0% - Chargeable income between NGN 800,000 and NGN 2,000,000: 15% - Chargeable income between NGN 2,000,000 and NGN 5,000,000: 18% - Chargeable income between NGN 5,000,000 and NGN 10,000,000: 21% - Chargeable income above NGN 10,000,000: 23%  The first NGN 800,000 is therefore tax-free.

### para-fact-01-b

**Prompt:** Which tax bands apply to an individual in 2026, and what is the rate for each?

**Before:** Chargeable income up to 800,000 is taxed at 0%. The next 2,200,000 (800,000 to 3,000,000) is taxed at 15%; the next 9,000,000 (3,000,000 to 12,000,000) at 18%; the next 13,000,000 (12,000,000 to 25,000,000) at 21%; the next 25,000,000 (25,000,000 to 50,000,000) at 23%; and anything above 50,000,000 at 25%.

**After:** In 2026, the first NGN 800,000 of chargeable income is taxed at 0%; the next NGN 2,200,000 (NGN 800,000 zero-rate income plus NGN 1,400,000 of the next band) at 15%; the next NGN 9,000,000 (NGN 2,200,000 already taxed plus NGN 6,800,000 of the next band) at 18%; the next NGN 13,000,000 (NGN 9,000,000 already taxed plus NGN 4,000,000 of the next band) at 21%; the next NGN 25,000,000 (NGN 13,000,000 already taxed plus NGN 12,000,000 of the next band) at 23%; and anything above NGN 50,000,000 at 25%.

### para-fact-01-c

**Prompt:** 2026 PIT bands + rates?

**Before:** Here are the bands for 2026: chargeable income up to 800,000 is taxed at 0%; the next 2,200,000 (800,000 to 3,000,000) at 15%; the next 9,000,000 (3,000,000 to 12,000,000) at 18%; the next 13,000,000 (12,000,000 to 25,000,000) at 21%; the next 25,000,000 (25,000,000 to 50,000,000) at 23%; and anything above 50,000,000 at 25%. The first 800,000 is therefore tax-free.

**After:** Here are the bands for 2026: chargeable income up to NGN 800,000 is taxed at 0%; the next NGN 2,200,000 (NGN 800,000 to NGN 3,000,000) at 15%; the next NGN 9,000,000 (NGN 3,000,000 to NGN 12,000,000) at 18%; the next NGN 13,000,000 (NGN 12,000,000 to NGN 25,000,000) at 21%; the next NGN 25,000,000 (NGN 25,000,000 to NGN 50,000,000) at 23%; and anything above NGN 50,000,000 at 25%.

### para-fact-01-d

**Prompt:** I'm updating my payroll spreadsheet and need to confirm the personal income tax rates for 2026, from the first band to the highest. Can you list them all?

**Before:** Here are the personal income tax bands for 2026, with the tax rate for each band:  - Chargeable income up to NGN 800,000: 0% - Chargeable income between NGN 800,000 and NGN 2,000,000: 15% - Chargeable income between NGN 2,000,000 and NGN 5,000,000: 18% - Chargeable income between NGN 5,000,000 and NGN 10,000,000: 21% - Chargeable income between NGN 10,000,000 and NGN 25,000,000: 23% - Chargeable income above NGN 25,000,000: 25%  The first NGN 800,000 is therefore tax-free.

**After:** Here are the personal income tax bands for 2026, with the tax rate for each band:  - Chargeable income up to NGN 800,000: 0% - Chargeable income between NGN 800,000 and NGN 2,000,000: 15% - Chargeable income between NGN 2,000,000 and NGN 5,000,000: 18% - Chargeable income between NGN 5,000,000 and NGN 10,000,000: 21% - Chargeable income above NGN 10,000,000: 23%  The first NGN 800,000 is therefore tax-free, and the tax on the next NGN 2,200,000 (the portion between NGN 800,000 and NGN 10,000,000) is calculated using the 15% band plus the 18% band.

### para-fact-01-e

**Prompt:** Someone said the top personal income tax rate for 2026 is 30%. Is that correct, and what are the bands?

**Before:** Yes, that is correct. The Fourth Schedule table of the Nigeria Tax Act 2025 shows that the tax table applies to chargeable income up to 800,000, with the first 800,000 at 0%, the next 2,200,000 (Nigeria Civil Service salary) at 15%, and every tier above 3,000,000 at 18%. The 30% band is therefore the fourth tier, and the zero band is the first 800,000.

**After:** Yes, that is correct. The top personal income tax rate for 2026 is 30%, applied to the portion of income above the previous bands. The first NGN 800,000 is taxed at 0%; the next NGN 2,200,000 (the next 1,400,000) is taxed at 15%; the next NGN 9,000,000 (the next 2,600,000) is taxed at 18%; the next NGN 13,000,000 (the next 3,400,000) is taxed at 21%; the next NGN 25,000,000 (the next 5,000,000) is taxed at 23%; and anything above NGN 50,000,000 is taxed at 25%.

### para-fact-02-a

**Prompt:** How is rent relief calculated, and is there a cap?

**Before:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### para-fact-02-b

**Prompt:** How does the rent relief work, and is there a maximum?

**Before:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### para-fact-02-c

**Prompt:** Rent relief: formula and cap?

**Before:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### para-fact-02-d

**Prompt:** I want to understand the rent relief fully before I claim it in my return: how is it computed and what is the maximum amount allowed?

**Before:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** Rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### para-fact-02-e

**Prompt:** A friend says rent relief gives you 20% back of whatever rent you pay, with no limit. Is that true?

**Before:** No - rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

**After:** No - rent relief is 20% of annual rent paid, capped at NGN 500,000, whichever is lower. The actual rent must be accurately declared and evidence may be required.

### para-fact-03-a

**Prompt:** Which deductions can reduce my chargeable income under the Nigeria Tax Act 2025?

**Before:** Under section 30 of the Nigeria Tax Act 2025, reliefs such as pension, NHF, NHIS, life insurance, mortgage interest, and voluntary pension contributions reduce your chargeable income. The relief must be claimed in writing and evidence may be required for some claims.

**After:** Under section 30 of the Nigeria Tax Act 2025, reliefs such as pension, NHF, NHIS, life insurance, mortgage interest, and voluntary pension contributions reduce your chargeable income. The relief must be claimed in writing and evidence may be required for some claims.

### para-fact-03-b

**Prompt:** What things can reduce my income before tax is calculated?

**Before:** Your chargeable income is the income after reliefs such as pension, NHF, NHIS, life insurance, mortgage interest and voluntary pension contributions. Reliefs are claimed in writing and evidence may be required.

**After:** Your chargeable income is the income after reliefs such as pension, NHF, NHIS, life insurance, mortgage interest and voluntary pension contributions. Reliefs are claimed in writing and evidence may be required.

### para-fact-03-c

**Prompt:** List eligible deductions?

**Before:** Eligible deductions are rent paid, pension contributions, NHF and NHIS contributions, life insurance and mortgage interest, and voluntary pension contributions.

**After:** Eligible deductions are rent paid, pension contributions, NHF and NHIS contributions, life insurance and mortgage interest, and voluntary pension contributions. The actual amount claimed must be supported by evidence.

### para-fact-03-d

**Prompt:** I'm reviewing what I can legitimately claim this year. Please list the deduction categories available to individuals under the current tax law.

**Before:** Under the Fourth Schedule of the Nigeria Tax Act 2025, eligible deductions for individuals include: pension contributions, interest on a home loan, life insurance and annuity premiums, NHF and NHIS contributions, a voluntary pension contribution, rent relief, and payments for a mortgage on a home you live in.

**After:** Under the Fourth Schedule of the Nigeria Tax Act 2025, eligible deductions for individuals include: pension contributions, interest on a home loan, life insurance and annuity premiums, NHF and NHIS contributions, a voluntary pension contribution, rent relief, and payments for a mortgage on a home you live in.

### para-fact-03-e

**Prompt:** Someone mentioned school fees and house rent as tax deductions. Which deductions actually exist under the 2025 Act?

**Before:** Under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, eligible deductions include pension, life insurance, and mortgage interest on a home you live in. Rent relief is capped at 20% of the annual rent paid, and a VAT certificate is required for the claim.

**After:** Under section 30(2)(a) of the Nigeria Tax Act 2025, eligible deductions include pension, life insurance, and mortgage interest on a home; voluntary pension; interest on a loan for developing an owner-occupied home; and rent relief. The rent relief is 20% of annual rent paid, capped.

### para-fact-04-a

**Prompt:** I earn the national minimum wage of NGN 70,000 a month. Do I pay income tax?

**Before:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage, and the tax is therefore zero.

**After:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage, because the Fourth Schedule tax table applies only to individuals with chargeable income above NGN 800,000. Earnings at the minimum wage are therefore outside the taxable income of a person under that table.

### para-fact-04-b

**Prompt:** I receive 70k every month, which is the minimum wage. Will tax be collected from me?

**Before:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage. Earnings at the minimum wage are taxed at the rate applicable to the first NGN 800,000 zeroed out, and the tax is due only if chargeable income exceeds NGN 800,000.

**After:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage. Earnings at the minimum wage are taxed at the rate applicable to the first NGN 800,000 zeroed out, and the tax is due on the imposable income after that.

### para-fact-04-c

**Prompt:** 70k/month minimum wage - taxable?

**Before:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage. Earnings up to the zero rate are exempt from tax; the tax is only charged on income above that.

**After:** No - the Fourth Schedule tax table does not apply to a person earning the national minimum wage. Earnings up to the zero rate are exempt from tax; the tax is only charged on income above that.

### para-fact-04-d

**Prompt:** My monthly pay is exactly the national minimum wage (NGN 70,000). I want to know whether I am expected to pay income tax on it, and if so how much.

**Before:** No - the Fourth Schedule tax table does not apply to an individual earning the national minimum wage. Earnings at the minimum are taxed at the rate applicable to the first NGN 800,000 zeroed in, so nothing to pay.

**After:** No - if your monthly income is NGN 70,000, you are exempt from income tax on your chargeable income; the Fourth Schedule tax table does not apply to you.

### para-fact-04-e

**Prompt:** A colleague insists everyone earning above 30,000 a month pays tax, even at the minimum wage. Who is right?

**Before:** That colleague is wrong. The Fourth Schedule table applies to salaries above the national minimum wage - NGN 80,000 per month - and the tax is computed on the income in the band above that. Earnings at the minimum wage are therefore untaxed, and so is every amount of rent above the annual limit.

**After:** That colleague is wrong. The Fourth Schedule table applies to salaries above the national minimum wage - and the tax is computed on the income earned above that. A salary at the minimum wage is exempt from income tax; the tax table does not apply to it.

### para-fact-05-a

**Prompt:** When is PAYE deducted from salaries due to be remitted to the tax authority?

**Before:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

**After:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

### para-fact-05-b

**Prompt:** After my employer deducts PAYE from salary, when should the money be remitted?

**Before:** The employer remits PAYE to the state tax authority by the 10th day of the month following the month in which it was deducted. The employer is also liable for any tax deducted under section 51 of the Nigeria Tax Act 2025.

**After:** The employer remits PAYE to the state tax authority by the 10th day of the month following the month in which it was deducted. The employer is also liable for any tax deducted under section 51 of the Nigeria Tax Act 2025.

### para-fact-05-c

**Prompt:** PAYE remittance deadline?

**Before:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

**After:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

### para-fact-05-d

**Prompt:** I run payroll for a small company and want to get the compliance calendar right. What is the deadline for remitting PAYE after salaries are paid?

**Before:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted. The return for the month is filed by the 10th day of the following month.

**After:** PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted. The return for the month is filed on the LIRS e-Tax platform.

### para-fact-05-e

**Prompt:** Our accountant says PAYE for January salaries can be remitted any time in February up to the 21st. Is that correct?

**Before:** Yes - under section 51 of the Nigeria Tax Administration Act 2025, PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

**After:** Yes - under section 51 of the Nigeria Tax Administration Act 2025, PAYE deducted from salaries is remitted to the state tax authority by the 10th day of the month following the month in which it was deducted.

### para-fact-06-a

**Prompt:** What are the mandatory pension contribution rates for employers and employees?

**Before:** The mandatory rates are 10% of monthly emoluments by the employer and 8% by the employee. The rates may be revised upwards by agreement between the employer and the employee.

**After:** The mandatory rates are 10% of monthly emoluments by the employer and 8% by the employee. The rates may be revised upwards by agreement between the employer and the employee.

### para-fact-06-b

**Prompt:** How much do employer and worker contribute for pension?

**Before:** Under the Pension Reform Act 2014, the minimum rates for the Contributory Pension Scheme are 10% of monthly emoluments by the employer and 8% by the employee. The rates may be revised upwards by agreement between the employer and the employee.

**After:** Under the Pension Reform Act 2014, contributions are made by the employer and the employee into the National Housing Fund (NHF) and the Pension Fund Custodian of the employee. The minimum rates are 10% of monthly emoluments by the employer and 8% by the employee. The rates may be revised upwards by agreement.

### para-fact-06-c

**Prompt:** Pension contribution rates?

**Before:** The minimum rate is 10% of monthly emoluments by the employer and 8% by the employee. The rate may be revised upwards by agreement.

**After:** Pension contributions are made through the employer into the employee's RSA and must be approved by the employee. The rates are 10% of monthly emoluments by the employer and 8% by the employee, under section 30(2)(a) of the Nigeria Tax Act 2025.

### para-fact-06-d

**Prompt:** I'm setting up payroll for a new company. Under the Pension Reform Act, what are the minimum rates that the employer and the employee must contribute, and what does the employer need to maintain for staff?

**Before:** Under the Pension Reform Act 2014, the minimum rates for the Contributory Pension Scheme are 10% of monthly emoluments by the employer and 8% by the employee. The employer must remit the contributions to the employee's RSA by the 10th day of the month following the month in which they were deducted, and the employee's RSA is managed by a Pension Fund Administrator.

**After:** Under the Pension Reform Act 2014, the minimum rates for the Contributory Pension Scheme are 10% of monthly emoluments by the employer and 8% by the employee. The employer must remit the contributions to the employee's RSA by the 10th day of the month following the month in which they were deducted, and the employee's RSA is managed by a Pension Fund Administrator.

### para-fact-06-e

**Prompt:** Someone said employee pension contribution is 7.5% and employer 7.5%. Is that still correct?

**Before:** Yes, that is still correct. Under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, the employee's pension relief is 10% of monthly emoluments, and the employer contributes 10%; both must be deducted from the employee's emoluments and remitted to the Pension Fund.

**After:** Yes, that is still correct. Under section 30(2)(a)(iii) of the Nigeria Tax Act 2025, the employee's pension relief is 7.5% of monthly emoluments and the employer must remit it to the employee's RSA.

### para-fact-07-a

**Prompt:** What are the rules for making voluntary pension contributions?

**Before:** Voluntary pension contributions are made through your employer into your RSA and must be made in Naira. You notify your employer in writing of your intention and the amount, and the contribution is capped at one-third of your month's salary.

**After:** Voluntary pension contributions are made through your employer into your RSA and are capped at one-third of your month's salary. You notify your employer in writing of your intention and the amount.

### para-fact-07-b

**Prompt:** How does voluntary pension contribution work - what are the rules?

**Before:** Voluntary pension contributions are made in Naira through your employer into your RSA, and you notify your employer in writing of your intention and the amount. They can be made once a month, and you can make them only once a month.

**After:** Voluntary pension contributions are made in Naira through your employer into your RSA, and you notify your employer in writing of your intention and the amount. They must be made no more than one-third of your month's salary, and you can make them once a month, bi-monthly, or once every two months.

### para-fact-07-c

**Prompt:** VPC rules and limits?

**Before:** VPC stands for Voluntary Pension Contribution, and it is a contribution made by an employee to his own retirement savings account. The minimum VPC is 10% of monthly emoluments, and it may be revised upwards by the employee and his employer. A VPC is mandatory in the case of an employee earning the national minimum wage, and it is also mandatory for all other employees in the case of a pension insufficiency.

**After:** The VPC (Value-Added Tax) rules and limits are as follows:  - The tax authority may apply the VPC to any taxable person, and the person may be liable to a penalty for any objection. - The VPC is a zero-rate tax, and the relevant tax authority may refuse the deduction or set it at a lower amount where it is an inference. - A deduction is allowed for a loss, and the loss must be fully admitted and proved.

### para-fact-07-d

**Prompt:** I want to start making voluntary pension contributions this year. Please explain the rules: how much I can contribute, how often, and how the money moves into my account.

**Before:** Voluntary pension contributions are made through your employer into your RSA. You notify your employer in writing of your intention and the amount, and the contribution is capped at one-third of your month's salary, made once a month.

**After:** Voluntary pension contributions are made through your employer into your RSA. You notify your employer in writing of your intention and the amount, and the contribution is capped at one-third of your month's salary, made once a month.

### para-fact-07-e

**Prompt:** Someone says you can voluntarily contribute any amount, any number of times a month, directly to your PFA. Is that correct?

**Before:** No. Voluntary contribution is capped at one-third of the month's salary, made once a month, into your RSA through your employer. You notify your employer in writing and the employer remits it to your RSA.

**After:** No. Voluntary contribution is capped at one-third of the month's salary, made once a month, into your RSA through your employer. You notify your employer in writing and the employer remits it to your RSA.

### para-fact-08-a

**Prompt:** How are voluntary pension contributions taxed if I withdraw them early?

**Before:** Voluntary pension contributions are taxed at the point of withdrawal, with the option of a deferred withdrawal. If you withdraw the money before the age of 55, the tax stays on the contribution and the withdrawal is capped at one-third of the contribution. If you withdraw after 55, the tax is waived and the full amount is remitted to your pension fund.

**After:** Voluntary pension contributions are taxed at the point of withdrawal: the tax stays on the contribution and it is no longer deductible. If you make a voluntary contribution in one year, you can amend it to add or reduce the amount, but the amendment must be written in the form prescribed by the Pension Reform Act.

### para-fact-08-b

**Prompt:** If I withdraw my voluntary pension early, will it be taxed?

**Before:** No - early withdrawal of voluntary pension is exempt from income tax on the withdrawal, under section 30 of the Pension Reform Act 2014.

**After:** No - early withdrawal of voluntary pension is exempt from income tax on the withdrawal, under section 30 of the Nigeria Tax Act 2025.

### para-fact-08-c

**Prompt:** Early VPC withdrawal - tax?

**Before:** Withholding tax still applies: the employee's employer deducts it and remits to the state. A withdrawal of the pension before the age of 55 still requires the employer to remit the tax on the pension, as the pension is a taxed income.

**After:** Withholding tax still applies: the employee's employer deducts it and remits to the state. A withdrawal of the pension before the age of 58 still requires the employer to remit the tax on the pension, under section 30 of the Pension Reform Act 2014.

### para-fact-08-d

**Prompt:** I'm weighing voluntary pension contributions but may need the money within a few years. What is the tax treatment if I withdraw a voluntary contribution earlier than the long-term window?

**Before:** Voluntary contributions are taxed at the point of withdrawal: the tax remains on the contribution as if it were emoluments, and the relief claims are assessed separately. If you withdraw a voluntary contribution before the end of the one-year clock, the tax may be deducted by the employer and remitted to the relevant tax authority, and the relief may be allowed only if a claim is made in writing within two years after the end of the year of assessment.

**After:** Voluntary contributions are taxed at the point of withdrawal: the tax remains on the contribution as if it were an in-employment pension contribution, and the relief is claimed in writing within six years after the year of withdrawal. If you withdraw a voluntary contribution before the end of the one-year clock, the tax may be deducted by the employer and the relief may be refused, so the withdrawal should be made only if the relief is claimed in writing with evidence.

### para-fact-08-e

**Prompt:** A friend says money earned on voluntary pension contributions is never taxed at all, even if you withdraw after one year. Is that right?

**Before:** No - that is not right. Voluntary pension contributions are taxed on the income they represent, and the tax is deducted by the employer into your RSA. The one-third-of-the-month rule still applies: the employer deducts the tax within the month after the employee's salary is recorded, and the employee can make a voluntary contribution in writing to the employer. Withdrawing money from the pension is a separate transaction and is taxed at the point of withdrawal, not after the year of assessment.

**After:** No - that is not right. Voluntary pension contributions are taxed on the income they represent, and the tax is deducted at source. The tax is not released to your RSA until the year of assessment, and it is not claimed or set off against any liability in your own return.

### para-fact-09-a

**Prompt:** What do I need to do to claim a tax deduction, and can the authority ask for proof?

**Before:** To claim a tax deduction, you must file a valid claim in writing with your annual return. The claim must be supported by evidence, and the relevant tax authority may require you to produce that evidence.

**After:** To claim a tax deduction, you must file a valid claim in writing with your annual return. The claim must be supported by evidence, and the relevant tax authority may require you to produce that evidence.

### para-fact-09-b

**Prompt:** What do I need to claim my relief, and can they ask me for proof?

**Before:** You claim relief for the year of assessment to which it relates; the claim must be in writing in the prescribed form; and the evidence may be required by the relevant tax authority.

**After:** You claim relief for the year of assessment to which it relates; the claim must be in writing in the prescribed form; and the evidence may be required by the relevant tax authority.

### para-fact-09-c

**Prompt:** Claim requirements + evidence?

**Before:** Yes - under section 30 of the Nigeria Tax Act 2025, a claim for relief must be made in writing in the prescribed form, supported by documentary evidence. The evidence may include reliefs such as pension, life assurance, NHIS, NHF, and NBS contributions, rent, interest on a mortgage, and relief for the unemployed.

**After:** Yes - a claim must be made in writing in the prescribed form, supported by evidence; in Lagos it is filed on the LIRS e-Tax platform, and in other states through the state tax authority.

### para-fact-09-d

**Prompt:** Before I claim deductions in my return, I want to understand the formalities: how claims must be made and what happens if the tax authority questions them.

**Before:** A deduction or relief claim must be made in writing in the prescribed form, supported by evidence; the authority may then require documentary evidence and may refuse the deduction, or part of it, where it is absent or inadequate; it may also allow a set-off against any tax liability.

**After:** A deduction or relief claim must be made in writing in the prescribed form, supported by evidence; the authority may then require documentary evidence and may refuse the deduction, or part of it, where it is absent or inadequate; it may also allow a set-off against any tax liability.

### para-fact-09-e

**Prompt:** Someone says deductions are granted automatically once you qualify, with no paperwork. Is that correct?

**Before:** No - the claim is wrong. A deduction or relief is granted only after a claim is made in writing in the prescribed form, and the relevant tax authority may require documentary evidence in support of the claim. The authority may also refuse the deduction, or part of it, where the evidence is absent or inadequate.

**After:** No - the claim is wrong. A deduction or relief is granted only after a claim is made in writing in the prescribed form, and the relevant tax authority may require documentary evidence in support of the claim. The authority may also refuse the deduction, or part of it, where the evidence is absent or inadequate.

### para-fact-10-a

**Prompt:** If I overpay my tax, how do I get a refund?

**Before:** Overpaid tax is refunded after an audit by the relevant tax authority. You notify the relevant tax authority in writing within six years after the end of the year of assessment to which the refund relates, and the authority may refund the overpayment after deducting interest.

**After:** Overpaid tax is refunded after an audit by the relevant tax authority. You notify the relevant tax authority in writing within six years after the end of the year of assessment to which the refund relates, and the authority may refund the overpayment after deducting interest.

### para-fact-10-b

**Prompt:** If I pay more tax than I should, how do I collect the excess back?

**Before:** You notify your employer in writing and claim the refund; the claim must be made within six years after the end of the year of assessment to be allowed.

**After:** You notify your employer in writing and claim the refund; the claim must be made within six years after the end of the year of assessment to be allowed.

### para-fact-10-c

**Prompt:** Overpaid tax - refund process?

**Before:** Overpaid tax is refunded after an audit by the relevant tax authority, under section 55 of the Nigeria Tax Administration Act 2025. A refund is paid within 90 days of the authority's decision, and the claim for refund is made in writing within six years after the end of the year of assessment to which it relates.

**After:** Overpaid tax is refunded after an audit by the relevant tax authority, under section 55 of the Nigeria Tax Administration Act 2025. A refund is paid within 90 days of the authority's decision, and the claim for refund is written in the prescribed form. A refund claim is allowed only if it is made in the prescribed form and is supported by evidence.

### para-fact-10-d

**Prompt:** Suppose PAYE deducted during the year ends up higher than my final liability after reliefs. What is the process and the timelines for recovering the excess?

**Before:** Overpaid tax is remitted to the relevant state tax authority, and after audit by the tax authority, the excess is refunded or set off against any tax liability. The refund is paid within 90 days of the authority's decision, and the claim for refund is made in writing within six years after the end of the year of assessment.

**After:** Overpaid tax is remitted to the relevant state tax authority, and after audit by the tax authority, the excess is refunded or set off against any tax liability. The refund is paid within 90 days of the authority's decision, and the claim for refund must be made in writing within six years after the end of the year of assessment to which it relates.

### para-fact-10-e

**Prompt:** Someone says overpaid tax is never refunded, only credited forever. What does the law actually provide?

**Before:** Overpaid tax is refunded after an audit by the relevant tax authority, under section 55 of the Nigeria Tax Administration Act 2025. A refund is fully paid within 90 days of the authority's decision, with the option of a set-off against any tax liability. A refund claim is allowed only if it is made in writing within six years after the end of the year of assessment to which it relates.

**After:** Overpaid tax is refunded after an audit by the relevant tax authority, under section 55 of the Nigeria Tax Administration Act 2025. A refund is fully paid within 90 days of the authority's decision, with the option of a set-off against any tax liability. A refund claim is allowed only if it is made in writing within six years after the end of the year of assessment to which it relates.

### para-fact-11-a

**Prompt:** Where and how do I file my annual income tax return and claim reliefs?

**Before:** File your annual return on the relevant state tax authority platform - LIRS e-Tax for Lagos State, the Federal e-Tax Form on the Nigeria Tax Authority (NTA) platform, or the state platform of your choice. The return is due by the end of the year of assessment, and you must claim reliefs such as pension, life insurance, NHIS, and voluntary pension contributions.

**After:** File your annual return on the relevant state tax authority platform - LIRS e-Tax for Lagos State, the Federal e-Tax Form on the Nigeria Tax Authority (NTA) platform, or the state platform of your choice. The return is due by the end of the year of assessment, and you must claim reliefs such as pension, life insurance, NHIS, and voluntary pension contributions.

### para-fact-11-b

**Prompt:** Where do I file my tax return and put my relief claims?

**Before:** File your annual return on the relevant state tax authority platform - LIRS e-Tax for Lagos State, the National Portal for other states, and the LIRS e-Tax App for both Lagos State and other states. The return is due by the end of the year of assessment, and the claim of relief must be written in the prescribed form.

**After:** File your annual return on the relevant state tax authority platform - LIRS e-Tax for Lagos State, the Nigeria Tax App for personal income tax, and the state tax platform for other states. The claim must be written in the prescribed form (Tax Form A) and supported with evidence.

### para-fact-11-c

**Prompt:** Filing channel for relief claims?

**Before:** Relief claims are made through your annual return, not through a separate relief fund. The claim must be written in the prescribed form (Tax Form A) and supported by evidence such as a pension statement or a rent certificate. The claim must also pass the "reasonable" test - the evidence must be what it is, and the deduction must be what you actually pay.

**After:** Relief claims are made through your annual return, not through a separate relief payment. The claim must be written in the prescribed form (Tax Form A) and supported by evidence such as a pension statement or a rent certificate.

### para-fact-11-d

**Prompt:** I'm preparing to file this year. Which platform and form do I use for my annual return, and where do relief claims go?

**Before:** Your annual return is filed on the LIRS e-Tax platform using the Lagos State Form LIRS-2026. Relief claims go through your employer into your refund claim form, and the claim must be written in the prescribed form.

**After:** Your annual return is filed on the LIRS e-Tax platform using the Lagos State Form LIRS-2026. Relief claims go in the prescribed form, and evidence of the claim must be uploaded for the claim to be accepted.

### para-fact-11-e

**Prompt:** A friend says relief claims are filed separately in a special office, not in the annual return. Is that true?

**Before:** No - relief claims are still made through the annual return, not separately. The claim must be written in the prescribed form (Tax Form A) and supported by evidence; the claim is allowed only if it is true and just.

**After:** No - relief claims are still made through the annual return, not separately. The claim must be written in the prescribed form (Tax Form A) and supported by evidence; in Lagos it is filed on the LIRS e-Tax platform.

### para-fact-12-a

**Prompt:** Can I still claim the consolidated relief allowance?

**Before:** Yes - the consolidated relief allowance is still optional and you can claim it even if PAYE was already deducted.

**After:** Yes - the consolidated relief allowance is still optional and you can claim it even if PAYE was already deducted.

### para-fact-12-b

**Prompt:** Is the consolidated relief allowance still there?

**Before:** Yes - the consolidated relief allowance no longer exists. The Nigeria Tax Act 2025 contains no personal relief or consolidated relief allowance concept: relief now comes through the N800,000 zero-rate income plus eligible deductions such as pension and NHF contributions, NHIS, life insurance, mortgage interest and rent.

**After:** Yes - the consolidated relief allowance no longer exists. The Nigeria Tax Act 2025 contains no personal relief or consolidated relief allowance concept: relief now comes through the N800,000 zero-rate income plus eligible deductions such as pension and NHF contributions, NHIS, life insurance, mortgage interest and rent.

### para-fact-12-c

**Prompt:** CRA still exists?

**Before:** The Nigeria Revenue Service (NIRS) is the tax authority for personal income tax in Nigeria. The Centre for Revenue Administration (CRA) no longer exists; it was replaced by the NIRS in 2018.

**After:** The Nigeria Revenue Service (NIRS) is the tax authority for personal income tax in Nigeria. The Centre for Revenue Administration (CRA) no longer exists; it was replaced by the NIRS in 2018.

### para-fact-12-d

**Prompt:** Some older tax articles I found describe a consolidated relief allowance that reduces taxable income. Does that allowance still exist under the current law, and what replaced it?

**Before:** The consolidated relief allowance no longer exists. The Nigeria Tax Act 2025 contains no personal relief or consolidated relief allowance concept: relief now comes through the N800,000 zero-rate income plus eligible deductions such as pension and NHF contributions, NHIS, life insurance, mortgage interest and rent. LIRS confirms the old consolidated relief allowance has been replaced by a rent-based allowance and other eligible deductions.

**After:** The consolidated relief allowance no longer exists. The Nigeria Tax Act 2025 contains no personal relief or consolidated relief allowance concept: relief now comes through the N800,000 zero-rate income plus eligible deductions such as pension and NHF contributions, NHIS, life insurance, mortgage interest and rent. LIRS confirms the old consolidated relief allowance has been replaced by a rent-based allowance and other eligible deductions.

### para-fact-12-e

**Prompt:** Someone says the CRA still applies alongside rent relief. Is that correct?

**Before:** Yes, that is correct. Rent relief still comes off the annual rent actually paid, and the claim is made in writing in the prescribed form. The Nigeria Tax Act 2025 still contains the Rent Relief Schedule, and the claim must be supported with evidence.

**After:** Yes, that is correct. Rent relief still comes off the annual rent actually paid, and the claim is made in writing in the prescribed form. The Nigeria Tax Act 2025 still contains the Rent Relief Schedule, and the claim must be supported with evidence.
