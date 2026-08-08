# Policy MCC-02: High-Risk Merchant Category Code

**Category:** high_risk_mcc

## Definition
The transaction's ISO 18245 Merchant Category Code (MCC) falls in
FinSightAI's high-risk set: **7995** (Gambling/Betting), **6051**
(Cryptocurrency/Virtual Currency), **6012** (Financial Institutions/Wire
Transfer), or **0000** (Unassigned/Unverified Gateway).

## Weight
Membership in the high-risk MCC set contributes **+0.35** to the
rule-based risk score. Reference risk weights for other common codes:
Groceries (5411) 0.05, Fast Food (5814) 0.10, Utilities (4899) 0.02,
Real Estate/Rent (6513) 0.01, Entertainment (7832) 0.15, Department
Stores (5311) 0.25, Taxicabs/Rideshare (4121) 0.15, General Retail
(5999) 0.20.

## Why this indicates fraud
Gambling, crypto, and wire-transfer channels are the fastest routes to
convert a stolen card's balance into cash or an untraceable asset before
the fraud is detected and the card is frozen. An unclassified/unverified
gateway code (0000) means the transaction didn't pass through normal
merchant categorization at all, which is itself a red flag for a
non-standard payment processor.

## What is NOT sufficient on its own
A transaction with a high-risk MCC code but a verified merchant, normal
amount, and low-risk category context does not automatically clear the
0.50 flag threshold — 0.35 alone is below threshold. This code is
designed to combine with at least one other factor (unverified merchant,
risky category label, or elevated income ratio), consistent with the
"single factor should not flag" design principle documented directly in
FinSightAI's scoring function.
