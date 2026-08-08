"""
generate_data.py

Synthetic transaction dataset matching the real FinSightAI schema
(z1taz/FinSightAI: backend/app/models/transaction.py) — amount, category,
merchant, mcc_code, is_merchant_verified — instead of an invented schema.

Fraud cases are injected to match the actual risk factors used by
FinSightAI's detector (backend/app/services/fraud_detector.py):
unverified merchant, high-risk MCC code, high-risk category label, and
income-ratio spikes. This keeps the eval harness a real extension of
that system rather than a lookalike built on made-up features.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)

MONTHLY_INCOME_BASELINE = 400000.0  # matches FinSightAI's default

# Mirrors fraud_detector.py's CATEGORY_RISK_MAP / MCC_RISK_MAP
CATEGORIES = {
    "Groceries": {"mcc": "5411", "merchant_pool": ["Big Bazaar", "More Supermarket", "Reliance Fresh"]},
    "Dining Out": {"mcc": "5814", "merchant_pool": ["Starbucks", "McDonalds", "Local Diner"]},
    "Utilities": {"mcc": "4899", "merchant_pool": ["Electric Corp", "Airtel", "ACT Fibernet"]},
    "Rent/Mortgage": {"mcc": "6513", "merchant_pool": ["Property Management"]},
    "Entertainment": {"mcc": "7832", "merchant_pool": ["PVR Cinemas", "Netflix", "BookMyShow"]},
    "Shopping": {"mcc": "5311", "merchant_pool": ["Amazon", "Myntra", "Croma"]},
    "Travel": {"mcc": "4121", "merchant_pool": ["Uber", "IndiGo", "MakeMyTrip"]},
    "Wire Transfer": {"mcc": "6012", "merchant_pool": ["Wire Transfer Dept", "Western Union"]},
    "Investment": {"mcc": "6051", "merchant_pool": ["Zerodha", "Groww"]},
    "Other": {"mcc": "0000", "merchant_pool": ["Unclassified Gateway"]},
}
NORMAL_CATEGORIES = ["Groceries", "Dining Out", "Utilities", "Shopping", "Entertainment"]


def _generate_normal_transactions(n_accounts: int, txns_per_account: int) -> pd.DataFrame:
    rows = []
    txn_id = 0
    for acct in range(n_accounts):
        for _ in range(txns_per_account):
            category = RNG.choice(NORMAL_CATEGORIES)
            info = CATEGORIES[category]
            amount = float(RNG.uniform(200, 6000))
            rows.append(
                {
                    "txn_id": f"T{txn_id:06d}",
                    "account_id": f"A{acct:05d}",
                    "amount": amount,
                    "category": category,
                    "merchant": RNG.choice(info["merchant_pool"]),
                    "mcc_code": info["mcc"],
                    "is_merchant_verified": True,
                    "monthly_income_baseline": MONTHLY_INCOME_BASELINE,
                    "fraud_label": 0,
                    "fraud_type": "none",
                }
            )
            txn_id += 1
    return pd.DataFrame(rows)


def _inject_unverified_high_risk_mcc(df: pd.DataFrame, n_cases: int) -> pd.DataFrame:
    """Unverified merchant (+0.40) + high-risk MCC (+0.35) = 0.75, clears 0.50 alone."""
    accounts = RNG.choice(df["account_id"].unique(), size=n_cases, replace=False)
    txn_start = int(df["txn_id"].str[1:].astype(int).max()) + 1
    rows = []
    for acct in accounts:
        rows.append(
            {
                "txn_id": f"T{txn_start:06d}",
                "account_id": acct,
                "amount": float(RNG.uniform(1000, 5000)),
                "category": "Other",
                "merchant": "Unclassified Gateway",
                "mcc_code": "0000",
                "is_merchant_verified": False,
                "monthly_income_baseline": MONTHLY_INCOME_BASELINE,
                "fraud_label": 1,
                "fraud_type": "unverified_high_risk_mcc",
            }
        )
        txn_start += 1
    return pd.DataFrame(rows)


def _inject_high_income_ratio(df: pd.DataFrame, n_cases: int) -> pd.DataFrame:
    """Verified merchant, normal MCC, but amount >= 80% of monthly income (+0.25) is
    alone NOT enough to clear 0.50 — needs a second signal, so pair with a
    moderately risky category to cross the threshold."""
    accounts = RNG.choice(df["account_id"].unique(), size=n_cases, replace=False)
    txn_start = int(df["txn_id"].str[1:].astype(int).max()) + 5000
    rows = []
    for acct in accounts:
        rows.append(
            {
                "txn_id": f"T{txn_start:06d}",
                "account_id": acct,
                "amount": MONTHLY_INCOME_BASELINE * float(RNG.uniform(0.85, 1.3)),
                "category": "Wire Transfer",
                "merchant": "Wire Transfer Dept",
                "mcc_code": "6012",
                "is_merchant_verified": True,
                "monthly_income_baseline": MONTHLY_INCOME_BASELINE,
                "fraud_label": 1,
                "fraud_type": "high_income_ratio_wire",
            }
        )
        txn_start += 1
    return pd.DataFrame(rows)


def _inject_gambling_mcc(df: pd.DataFrame, n_cases: int) -> pd.DataFrame:
    """High-risk MCC (gambling, +0.35) + risky category label (+0.15) = 0.50, right at threshold."""
    accounts = RNG.choice(df["account_id"].unique(), size=n_cases, replace=False)
    txn_start = int(df["txn_id"].str[1:].astype(int).max()) + 9000
    rows = []
    for acct in accounts:
        rows.append(
            {
                "txn_id": f"T{txn_start:06d}",
                "account_id": acct,
                "amount": float(RNG.uniform(2000, 8000)),
                "category": "Gambling",
                "merchant": "Offshore Betting Ltd",
                "mcc_code": "7995",
                "is_merchant_verified": True,
                "monthly_income_baseline": MONTHLY_INCOME_BASELINE,
                "fraud_label": 1,
                "fraud_type": "gambling_mcc",
            }
        )
        txn_start += 1
    return pd.DataFrame(rows)


def build_dataset(n_accounts: int = 400, txns_per_account: int = 20) -> pd.DataFrame:
    normal = _generate_normal_transactions(n_accounts, txns_per_account)
    fraud_parts = [
        _inject_unverified_high_risk_mcc(normal, n_cases=15),
        _inject_high_income_ratio(normal, n_cases=10),
        _inject_gambling_mcc(normal, n_cases=10),
    ]
    full = pd.concat([normal, *fraud_parts], ignore_index=True)
    return full


if __name__ == "__main__":
    df = build_dataset()
    out_path = "data/transactions.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} transactions ({df['fraud_label'].sum()} labeled fraud) to {out_path}")
    print(df["fraud_type"].value_counts())
