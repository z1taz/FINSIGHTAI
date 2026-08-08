# Policy MV-01: Unverified Merchant Entity

**Category:** unverified_merchant

## Definition
A transaction's merchant does not have a verified government Tax ID or
Legal Entity Identifier (LEI) on file. FinSightAI tracks this as the
boolean `is_merchant_verified` field on every transaction.

## Weight
`is_merchant_verified == False` contributes **+0.40** to the rule-based
risk score. This is the single largest individual weight in the scoring
formula — but it is still below the 0.50 flag threshold on its own,
meaning an unverified merchant alone is not sufficient to flag a
transaction. It requires at least one more contributing factor (a
high-risk MCC code, a risky category label, or an elevated income
ratio) to cross the threshold.

## Why this indicates fraud
Verified merchants have gone through registration checks; unverified
ones have not. Stolen-card fraud disproportionately routes through
merchants or payment gateways that skip that registration step, since
legitimate registered merchants have chargeback and compliance exposure
that fraud operations want to avoid.

## What is NOT sufficient on its own
A single unverified-merchant transaction from an otherwise low-risk
category (e.g. Groceries, Utilities) at a normal amount does not clear
the flag threshold by itself under this system. Small/local unverified
vendors are common and not inherently fraudulent — the score design
reflects that by requiring a second signal.
