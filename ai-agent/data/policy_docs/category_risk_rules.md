# Policy CAT-03: High-Risk Category Label

**Category:** high_risk_category

## Definition
The transaction is tagged with a category label FinSightAI treats as
elevated risk: **Wire Transfer**, **Gambling**, or **Betting**.

## Weight
Membership in this category set contributes **+0.15** to the
rule-based risk score. Reference weights for other categories:
Groceries 0.05, Dining Out 0.10, Utilities 0.02, Rent/Mortgage 0.01,
Entertainment 0.15, Shopping 0.25, Travel 0.35, Investment 0.40, Other
0.30.

## Why this indicates fraud
Category label risk is a coarser, complementary signal to MCC risk —
MCC-03 evidence — and the two often co-occur (a Wire Transfer category
label typically pairs with MCC 6012, a Gambling category label with MCC
7995). The category weight exists mainly to reinforce the MCC signal
rather than to flag on its own, since category labels are
self-declared/derived at the application layer while MCC is closer to
the raw payment-network data.

## What is NOT sufficient on its own
+0.15 alone is far below the 0.50 flag threshold. This factor almost
never flags a transaction by itself; it functions as a secondary
confirming signal, most meaningfully when it appears alongside a
matching MCC-02 high-risk-MCC flag or an elevated income ratio.
