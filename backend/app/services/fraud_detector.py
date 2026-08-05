import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
from typing import List, Tuple, Dict

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")

# ISO 18245 Merchant Category Code (MCC) & Category Risk Weights
MCC_RISK_MAP = {
    "5411": 0.05, # Grocery Stores
    "5814": 0.10, # Fast Food / Restaurants
    "4899": 0.02, # Cable, Satellite, Internet Utilities
    "6513": 0.01, # Real Estate / Rent
    "7832": 0.15, # Motion Picture Theaters / Entertainment
    "5311": 0.25, # Department Stores / Shopping
    "4121": 0.15, # Taxicabs / Rideshare
    "6012": 0.85, # Financial Institutions / Wire Transfer
    "7995": 0.90, # Gambling / Betting Transactions
    "6051": 0.85, # Cryptocurrency / Virtual Currency
    "0000": 0.95, # Unassigned / Unverified Gateway
    "5999": 0.20  # General Retail
}

CATEGORY_RISK_MAP = {
    "Groceries": 0.05,
    "Dining Out": 0.10,
    "Utilities": 0.02,
    "Rent/Mortgage": 0.01,
    "Entertainment": 0.15,
    "Shopping": 0.25,
    "Travel": 0.35,
    "Wire Transfer": 0.85,
    "Investment": 0.40,
    "Other": 0.30
}

def extract_features(transactions: List[Dict], monthly_income_baseline: float = 400000.0) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    if df.empty:
        return pd.DataFrame(columns=["amount", "income_ratio", "is_merchant_verified", "mcc_risk", "category_risk"])
    
    # Ensure amount column
    if "amount" not in df.columns:
        df["amount"] = 0.0
        
    # 1. Income Ratio (Single transaction relative to monthly baseline)
    df["income_ratio"] = df["amount"] / monthly_income_baseline
    
    # 2. Merchant Verification (1 = Verified Entity, 0 = Unverified Entity)
    if "is_merchant_verified" not in df.columns:
        df["is_merchant_verified"] = 1
    else:
        df["is_merchant_verified"] = df["is_merchant_verified"].astype(int)
    
    # 3. MCC Code Risk Mapping
    if "mcc_code" not in df.columns:
        df["mcc_code"] = "5999"
    df["mcc_risk"] = df["mcc_code"].map(lambda code: MCC_RISK_MAP.get(str(code), 0.20))
    
    # 4. Category Risk Mapping
    if "category" not in df.columns:
        df["category"] = "Other"
    df["category_risk"] = df["category"].map(lambda c: CATEGORY_RISK_MAP.get(c, 0.30))
    
    # Select Cybersecurity Feature Set (Replaces arbitrary time-of-day metrics)
    features = df[["amount", "income_ratio", "is_merchant_verified", "mcc_risk", "category_risk"]].copy()
    return features

class FraudDetector:
    def __init__(self):
        self.model = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
            except Exception:
                self.model = None
                
    def save_model(self):
        if self.model:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
                
    def train(self, transactions: List[Dict], monthly_income_baseline: float = 400000.0) -> float:
        features = extract_features(transactions, monthly_income_baseline)
        if len(features) < 20:
            self.model = IsolationForest(contamination=0.10, random_state=42)
            self.model.fit(features)
            self.save_model()
            return 1.0
            
        self.model = IsolationForest(contamination=0.10, random_state=42, n_estimators=150)
        self.model.fit(features)
        self.save_model()
        
        preds = self.model.predict(features)
        contamination_pct = np.sum(preds == -1) / len(preds)
        return float(contamination_pct)
        
    def predict(self, transactions: List[Dict], monthly_income_baseline: float = 400000.0) -> List[Tuple[int, float]]:
        features = extract_features(transactions, monthly_income_baseline)
        
        # High-risk MCC codes (gambling, crypto, wire, unclassified gateway)
        HIGH_RISK_MCC = {"7995", "6051", "6012", "0000"}
        
        results = []
        for i, tx in enumerate(transactions):
            amount = float(tx.get("amount", 0))
            category = str(tx.get("category", ""))
            mcc = str(tx.get("mcc_code", "5999"))
            is_verified = bool(tx.get("is_merchant_verified", True))
            
            income_ratio = amount / monthly_income_baseline
            
            # ============================================================
            #  WEIGHTED RISK SCORING (replaces naive OR-gate)
            #
            #  The key principle: a SINGLE factor alone should not flag.
            #  Buying gold from Tanishq (verified, normal MCC) for $2,000
            #  is a legitimate purchase even though it's expensive.
            #  But $2,000 from an UNVERIFIED merchant with MCC-0000 is
            #  extremely suspicious because MULTIPLE risk factors combine.
            #
            #  Risk score accumulates from independent factors:
            #   - Unverified merchant entity     → +0.40
            #   - High-risk MCC code             → +0.35
            #   - High-risk category label       → +0.15
            #   - Income ratio (scaled)          → +0.00 to +0.25
            #
            #  Final score >= 0.50 → FLAGGED
            #  This means you need at least 2 risk factors to get flagged.
            # ============================================================
            
            risk_score = 0.0
            
            # Factor 1: Merchant Entity Verification
            # Unverified = no government Tax ID / LEI registered
            if not is_verified:
                risk_score += 0.40
            
            # Factor 2: MCC Code Risk
            # Gambling (7995), Crypto (6051), Wire (6012), Unclassified (0000)
            if mcc in HIGH_RISK_MCC:
                risk_score += 0.35
            
            # Factor 3: Category Label Risk
            if category in ["Wire Transfer", "Gambling", "Betting"]:
                risk_score += 0.15
            
            # Factor 4: Income Ratio (graduated scale)
            # Spending 80%+ of monthly income in one shot is always a red flag
            # But 30% from a verified store is just a big purchase
            if income_ratio >= 0.80:
                risk_score += 0.25
            elif income_ratio >= 0.50:
                risk_score += 0.15
            elif income_ratio >= 0.30:
                risk_score += 0.08
            
            # --- Decision ---
            if risk_score >= 0.50:
                # Multiple risk factors combined → FLAGGED
                # Cap at 0.96 for display
                final_score = min(0.50 + (risk_score - 0.50) * 1.5, 0.96)
                results.append((1, float(final_score)))
                continue
            
            # If model is loaded, let Isolation Forest evaluate the feature vector
            if self.model is not None:
                feat_row = features.iloc[[i]]
                pred = self.model.predict(feat_row)[0]
                raw = self.model.decision_function(feat_row)[0]
                score = 1.0 / (1.0 + np.exp(8.0 * (raw + 0.05)))
                
                # Blend: add the rule-based risk_score as a small nudge
                blended = score * 0.7 + risk_score * 0.3
                is_fraud = 1 if (pred == -1 and blended >= 0.50) else 0
                results.append((is_fraud, float(blended)))
            else:
                # No model trained yet, use rule score as-is
                results.append((0, float(risk_score)))
                
        return results

fraud_detector = FraudDetector()

