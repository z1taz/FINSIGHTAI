# Policy INC-04: Income Ratio Threshold

**Category:** income_ratio

## Definition
The transaction amount as a fraction of the account's monthly income
baseline: `income_ratio = amount / monthly_income_baseline`.

## Weight (graduated)
- `income_ratio >= 0.80` → **+0.25**
- `income_ratio >= 0.50` → **+0.15**
- `income_ratio >= 0.30` → **+0.08**
- below 0.30 → **+0.00**

Even at the maximum tier, +0.25 alone is below the 0.50 flag threshold.

## Why this indicates fraud
Spending 80%+ of a stated monthly income in a single transaction is
unusual account behavior regardless of merchant type — it's a proxy for
"this transaction is far outside the account's normal financial
footprint." On its own this could be a legitimate large purchase (a
wedding, a laptop, a large rent payment), which is exactly why the
weight is capped well below the flag threshold and the formula requires
a second, more merchant-specific signal (verification status, MCC risk,
or category risk) before flagging.

## What is NOT sufficient on its own
A high-income-ratio transaction at a verified merchant with a low-risk
MCC and category (e.g. a large but verified appliance purchase) will not
clear 0.50 by this factor alone. This is the intended behavior — the
threshold exists to catch financial-footprint outliers, not to penalize
large legitimate purchases.
