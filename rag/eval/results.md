# Retrieval & answer evaluation results

Corpus: **10 documents / 46 chunks** · Questions: **22 answerable + 6 unanswerable** · Avg latency: **24.9 ms/query**

| Metric | Score | Meaning |
|---|---|---|
| Recall@2 (docs) | 100% | gold source in top-2 retrieved documents |
| Recall@5 (docs) | 100% | gold source in top-5 |
| MRR@5 | 0.909 | how high the right chunk ranks |
| nDCG@5 | 0.517 | graded ranking quality |
| Abstention accuracy | 100% (6/6) | out-of-domain questions correctly refused |
| False refusals | 0/22 | answerable questions we failed to answer |
| Answer groundedness | 100% | every answer sentence traceable to a cited chunk |
| Correct source cited | 100% | citations include the gold document |

## Per-question detail

| QID | Type | Question | Gold doc | Doc rank | Abstained? |
|---|---|---|---|---|---|
| q01 | answerable | How much deposit is insured by DICGC? | dicgc_insurance | 2 | ✅ answered |
| q02 | answerable | Is my money in a small finance bank safe? Is Suryoday insure | small_finance_banks | 2 | ✅ answered |
| q03 | answerable | 8.5% p.a. ka matlab kya hai? | fd_basics | 1 | ✅ answered |
| q04 | answerable | If I put 1 lakh for 1 year at 8.5% quarterly compounding, ho | compounding_maturity | 1 | ✅ answered |
| q05 | answerable | What happens if I break my FD before 12 months? | premature_withdrawal | 1 | ✅ answered |
| q06 | answerable | Does the bank deduct tax on FD interest? | tax_tds | 2 | ✅ answered |
| q07 | answerable | Senior citizen ko FD par kitni extra interest milti hai? | senior_citizen_rates | 1 | ✅ answered |
| q08 | answerable | What tax deduction do senior citizens get on deposit interes | section_80ttb | 1 | ✅ answered |
| q09 | answerable | Monthly interest payout chahiye ya ek saath end mein? Kya fa | cumulative_vs_payout | 1 | ✅ answered |
| q10 | answerable | Who pays the deposit money to my nominee if something happen | nomination_kyc | 1 | ✅ answered |
| q11 | answerable | Which documents do I need to open a fixed deposit? | nomination_kyc | 1 | ✅ answered |
| q12 | answerable | Are Ujjivan and Jana bank deposits covered by deposit insura | dicgc_insurance | 1 | ✅ answered |
| q13 | answerable | If a bank fails, how long does it take to get my insured mon | dicgc_insurance | 1 | ✅ answered |
| q14 | answerable | What is Form 15G and when should I submit it? | tax_tds | 1 | ✅ answered |
| q15 | answerable | Why do small finance banks give higher FD rates than big ban | small_finance_banks | 1 | ✅ answered |
| q16 | answerable | ₹5 lakh se zyada jama karu to kitna safe hai? | dicgc_insurance | 1 | ✅ answered |
| q17 | answerable | What does quarterly compounding mean for my FD? | compounding_maturity | 1 | ✅ answered |
| q18 | answerable | Can I withdraw only part of my FD early? | premature_withdrawal | 1 | ✅ answered |
| q19 | answerable | How much TDS threshold applies for senior citizens from 2025 | tax_tds | 2 | ✅ answered |
| q20 | answerable | Does nomination mean the nominee keeps all the money legally | nomination_kyc | 1 | ✅ answered |
| q21 | answerable | 8.5% rate par effective yield kitna hota hai quarterly compo | compounding_maturity | 1 | ✅ answered |
| q22 | answerable | PAN dena zaroori hai FD ke liye? PAN na do to kya hoga? | nomination_kyc | 1 | ✅ answered |
| q23 | unanswerable | Should I invest in mutual funds instead of FD? | — | — | ✅ refused |
| q24 | unanswerable | What is the current stock price of SBI? | — | — | ✅ refused |
| q25 | unanswerable | Bitcoin mein paisa lagana chahiye? | — | — | ✅ refused |
| q26 | unanswerable | How do I get a personal loan at a low interest rate? | — | — | ✅ refused |
| q27 | unanswerable | Which credit card gives the best cashback? | — | — | ✅ refused |
| q28 | unanswerable | What is the weather in Gorakhpur today? | — | — | ✅ refused |
