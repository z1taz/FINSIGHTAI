"""
detector.py

This is a direct port of the real detection logic from
z1taz/FinSightAI (backend/app/services/fraud_detector.py) — same MCC risk
map, same category risk map, same weighted risk-scoring formula, same
0.50 flag threshold, same 70/30 blend with the Isolation Forest score.
It is NOT a from-scratch reimplementation with different numbers; the
constants below are copied so this eval harness is testing the actual
system, not a lookalike.

The one thing intentionally NOT ported: the real service predicts on
one transaction at a time via a FastAPI endpoint. Here it's vectorized
over a full CSV for batch scoring, since the eval harness needs to run
against many transactions at once.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# --- Ported verbatim from FinSightAI's fraud_detector.py ---
MCC_RISK_MAP = {
    "5411": 0.05, "5814": 0.10, "4899": 0.02, "6513": 0.01,
    "7832": 0.15, "5311": 0.25, "4121": 0.15, "6012": 0.85,
    "7995": 0.90, "6051": 0.85, "0000": 0.95, "5999": 0.20,
}
CATEGORY_RISK_MAP = {
    "Groceries": 0.05, "Dining Out": 0.10, "Utilities": 0.02,
    "Rent/Mortgage": 0.01, "Entertainment": 0.15, "Shopping": 0.25,
    "Travel": 0.35, "Wire Transfer": 0.85, "Investment": 0.40,
    "Other": 0.30,
}
HIGH_RISK_MCC = {"7995", "6051", "6012", "0000"}
FLAG_THRESHOLD = 0.50


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Same 5-feature set as FinSightAI's extract_features()."""
    out = pd.DataFrame(index=df.index)
    out["amount"] = df["amount"]
    out["income_ratio"] = df["amount"] / df["monthly_income_baseline"]
    out["is_merchant_verified"] = df["is_merchant_verified"].astype(int)
    out["mcc_risk"] = df["mcc_code"].astype(str).map(lambda c: MCC_RISK_MAP.get(c, 0.20))
    out["category_risk"] = df["category"].map(lambda c: CATEGORY_RISK_MAP.get(c, 0.30))
    return out


def _rule_risk_score(row: pd.Series) -> float:
    """Same weighted scoring as FinSightAI: needs 2+ factors to clear 0.50."""
    score = 0.0
    if not row["is_merchant_verified"]:
        score += 0.40
    if str(row["mcc_code"]) in HIGH_RISK_MCC:
        score += 0.35
    if row["category"] in ["Wire Transfer", "Gambling", "Betting"]:
        score += 0.15
    ratio = row["amount"] / row["monthly_income_baseline"]
    if ratio >= 0.80:
        score += 0.25
    elif ratio >= 0.50:
        score += 0.15
    elif ratio >= 0.30:
        score += 0.08
    return score


class FraudDetector:
    """Ports FinSightAI's FraudDetector.train()/predict() for batch use."""

    def __init__(self):
        self.model: IsolationForest | None = None

    def fit(self, df: pd.DataFrame) -> "FraudDetector":
        features = extract_features(df)
        n_estimators = 150 if len(features) >= 20 else 100
        self.model = IsolationForest(contamination=0.10, random_state=42, n_estimators=n_estimators)
        self.model.fit(features)
        return self

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        features = extract_features(df)
        out = df.copy()
        out = out.join(features.add_suffix("_feat"))

        rule_scores = df.apply(_rule_risk_score, axis=1)
        out["rule_risk_score"] = rule_scores

        flagged, blended_scores = [], []
        for i in range(len(df)):
            rscore = rule_scores.iloc[i]
            if rscore >= FLAG_THRESHOLD:
                # Rule score alone clears the bar — matches FinSightAI's early exit.
                final = min(0.50 + (rscore - 0.50) * 1.5, 0.96)
                flagged.append(True)
                blended_scores.append(final)
                continue

            if self.model is not None:
                feat_row = features.iloc[[i]]
                pred = self.model.predict(feat_row)[0]
                raw = self.model.decision_function(feat_row)[0]
                iso_score = 1.0 / (1.0 + np.exp(8.0 * (raw + 0.05)))
                blended = iso_score * 0.7 + rscore * 0.3
                flagged.append(pred == -1 and blended >= FLAG_THRESHOLD)
                blended_scores.append(blended)
            else:
                flagged.append(False)
                blended_scores.append(rscore)

        out["fraud_score"] = blended_scores
        out["flagged"] = flagged
        return out


def run_pipeline(transactions_path: str = "data/transactions.csv") -> pd.DataFrame:
    # mcc_code must stay a zero-padded string ("0000", "6012") — without this,
    # pandas infers it as int64 and "0000" silently becomes 0, which no longer
    # matches HIGH_RISK_MCC. Caught this by checking flagged counts against
    # expected fraud_type counts after the first run — worth keeping as a
    # regression check, not just a one-off fix.
    df = pd.read_csv(transactions_path, dtype={"mcc_code": str})
    detector = FraudDetector().fit(df)
    scored = detector.score(df)
    return scored.sort_values("fraud_score", ascending=False)


if __name__ == "__main__":
    result = run_pipeline()
    flagged = result[result["flagged"]]
    print(f"Flagged {len(flagged)} of {len(result)} transactions")
    print("Precision vs injected fraud_label:", round((flagged["fraud_label"] == 1).mean(), 3))
    print("Recall vs injected fraud_label:", round(result[result["fraud_label"] == 1]["flagged"].mean(), 3))
    print(flagged["fraud_type"].value_counts())
    flagged.to_csv("reports/sample_flagged.csv", index=False)
