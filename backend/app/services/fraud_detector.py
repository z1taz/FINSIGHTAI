import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
from typing import List, Tuple, Dict, Any, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")

# ISO 18245 Merchant Category Code (MCC) & Category Risk Weights
MCC_RISK_MAP = {
    "5411": 0.05,  # Grocery Stores
    "5814": 0.10,  # Fast Food / Restaurants
    "4899": 0.02,  # Cable, Satellite, Internet Utilities
    "6513": 0.01,  # Real Estate / Rent
    "7832": 0.15,  # Motion Picture Theaters / Entertainment
    "5311": 0.25,  # Department Stores / Shopping
    "4121": 0.15,  # Taxicabs / Rideshare
    "6012": 0.85,  # Financial Institutions / Wire Transfer
    "7995": 0.90,  # Gambling / Betting Transactions
    "6051": 0.85,  # Cryptocurrency / Virtual Currency
    "0000": 0.95,  # Unassigned / Unverified Gateway
    "5999": 0.20   # General Retail
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

HIGH_RISK_MCC = {"7995", "6051", "6012", "0000"}

def extract_features(transactions: List[Dict], monthly_income_baseline: float = 400000.0) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    if df.empty:
        return pd.DataFrame(columns=["amount", "income_ratio", "is_merchant_verified", "mcc_risk", "category_risk"])
    
    if "amount" not in df.columns:
        df["amount"] = 0.0
        
    df["income_ratio"] = df["amount"] / max(monthly_income_baseline, 1.0)
    
    if "is_merchant_verified" not in df.columns:
        df["is_merchant_verified"] = 1
    else:
        df["is_merchant_verified"] = df["is_merchant_verified"].astype(int)
    
    if "mcc_code" not in df.columns:
        df["mcc_code"] = "5999"
    df["mcc_risk"] = df["mcc_code"].map(lambda code: MCC_RISK_MAP.get(str(code), 0.20))
    
    if "category" not in df.columns:
        df["category"] = "Other"
    df["category_risk"] = df["category"].map(lambda c: CATEGORY_RISK_MAP.get(c, 0.30))
    
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

    def calculate_structured_risk(
        self,
        tx: Dict[str, Any],
        monthly_income_baseline: float = 400000.0,
        model_score_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate structured, additive risk factors.
        Every factor has an exact point allocation grounded in observable data.
        Returns:
            - total_score: 0 to 100
            - is_flagged: bool
            - risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
            - risk_factors: List[Dict] with exact point weights
            - counterfactuals: Sensitivity scenarios
        """
        amount = float(tx.get("amount", 0.0))
        category = str(tx.get("category", "Other"))
        mcc = str(tx.get("mcc_code", "5999"))
        is_verified = bool(tx.get("is_merchant_verified", True))
        device_id = tx.get("device_id")
        is_new_device = bool(tx.get("is_new_device", False) or (device_id and "NEW" in str(device_id).upper()))
        is_velocity_burst = bool(tx.get("is_velocity_burst", False) or tx.get("velocity_count", 1) > 2)
        location = str(tx.get("location", ""))
        is_geo_anomaly = bool(tx.get("is_geo_anomaly", False) or any(k in location.lower() for k in ["foreign", "unknown", "vpn", "proxy"]))
        
        income_ratio = amount / max(monthly_income_baseline, 1.0)
        
        factors = []
        raw_points = 0.0

        # Factor 1: Merchant Entity Verification (Deterministic Rule)
        if not is_verified:
            pts = 35.0
            raw_points += pts
            factors.append({
                "factor": "Unverified Merchant Entity",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": f"Merchant '{tx.get('merchant', 'Unknown')}' has no verified LEI or Tax ID registration."
            })
            
        # Factor 2: High-Risk MCC Classification (Deterministic Rule)
        if mcc in HIGH_RISK_MCC:
            mcc_weight = MCC_RISK_MAP.get(mcc, 0.85)
            pts = 30.0 * (mcc_weight / 0.90)
            raw_points += pts
            factors.append({
                "factor": f"High-Risk Merchant Code (MCC {mcc})",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": f"Associated with gambling, cryptocurrency, or unclassified payment gateway settlement."
            })
            
        # Factor 3: Income Ratio & Amount Deviation (Deterministic Rule)
        if income_ratio >= 0.80:
            pts = 25.0
            raw_points += pts
            factors.append({
                "factor": "Severe Amount Deviation (>80% monthly baseline)",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": f"Transaction amount represents {round(income_ratio * 100, 1)}% of customer's declared monthly income."
            })
        elif income_ratio >= 0.50:
            pts = 15.0
            raw_points += pts
            factors.append({
                "factor": "High Amount Deviation (50-80% monthly baseline)",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": f"Transaction amount represents {round(income_ratio * 100, 1)}% of customer's declared monthly income."
            })
        elif income_ratio >= 0.30:
            pts = 8.0
            raw_points += pts
            factors.append({
                "factor": "Moderate Amount Deviation (30-50% monthly baseline)",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": f"Transaction amount represents {round(income_ratio * 100, 1)}% of customer's declared monthly income."
            })

        # Factor 4: High-Risk Category Label (Deterministic Rule)
        if category in ["Wire Transfer", "Gambling", "Betting"]:
            pts = 15.0
            raw_points += pts
            factors.append({
                "factor": f"High-Risk Transaction Category ({category})",
                "points": round(pts, 1),
                "category": "deterministic_rule",
                "description": "Category involves irreversible fund transfers or wagering activity."
            })

        # Factor 5: Device Freshness Signal
        if is_new_device:
            pts = 20.0
            raw_points += pts
            factors.append({
                "factor": "Unrecognized / New Device Fingerprint",
                "points": round(pts, 1),
                "category": "entity_risk",
                "description": "First observation of hardware fingerprint for this customer profile."
            })

        # Factor 6: Transaction Velocity Anomaly
        if is_velocity_burst:
            pts = 18.0
            raw_points += pts
            factors.append({
                "factor": "Transaction Velocity Anomaly",
                "points": round(pts, 1),
                "category": "entity_risk",
                "description": "Multiple high-frequency settlement requests recorded in a compressed time window."
            })

        # Factor 7: Geographic / IP Routing Anomaly
        if is_geo_anomaly:
            pts = 12.0
            raw_points += pts
            factors.append({
                "factor": "Geographic / IP Anomaly",
                "points": round(pts, 1),
                "category": "entity_risk",
                "description": f"Routing origin '{location or 'Foreign/Proxy'}' deviates from customer primary locale."
            })

        # Model-derived Isolation Forest component
        model_score_pct = 0.0
        if model_score_override is not None:
            model_score_pct = model_score_override * 100.0
        elif self.model is not None:
            try:
                feat = extract_features([tx], monthly_income_baseline)
                raw = self.model.decision_function(feat)[0]
                model_score_pct = float(1.0 / (1.0 + np.exp(8.0 * (raw + 0.05))) * 100.0)
            except Exception:
                model_score_pct = 0.0

        if model_score_pct >= 50.0:
            iforest_pts = round((model_score_pct - 50.0) * 0.4, 1)
            if iforest_pts > 0:
                raw_points += iforest_pts
                factors.append({
                    "factor": "Isolation Forest Outlier Anomaly",
                    "points": iforest_pts,
                    "category": "model_derived",
                    "description": f"Unsupervised multi-dimensional spending space outlier (decision score {round(model_score_pct, 1)}/100)."
                })

        # Composite score calculation (clamped between 0 and 99)
        final_score = min(max(raw_points, 0.0), 99.0)
        
        # Risk level categorization
        if final_score >= 75.0:
            risk_level = "CRITICAL"
        elif final_score >= 50.0:
            risk_level = "HIGH"
        elif final_score >= 30.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_flagged = (final_score >= 50.0)

        # Counterfactual / Feature-Sensitivity Scenarios (Section 11)
        counterfactuals = []
        if not is_verified:
            cf_score = max(final_score - 35.0, 0.0)
            counterfactuals.append({
                "scenario": "If merchant entity were fully verified & registered",
                "estimated_risk_score": round(cf_score, 1),
                "delta": -35.0
            })
        if income_ratio >= 0.30:
            pts_saved = 25.0 if income_ratio >= 0.80 else (15.0 if income_ratio >= 0.50 else 8.0)
            cf_score = max(final_score - pts_saved, 0.0)
            counterfactuals.append({
                "scenario": "If transaction amount were within historical baseline (<10% income)",
                "estimated_risk_score": round(cf_score, 1),
                "delta": -round(pts_saved, 1)
            })
        if is_new_device:
            cf_score = max(final_score - 20.0, 0.0)
            counterfactuals.append({
                "scenario": "If device had prior trusted authentication history",
                "estimated_risk_score": round(cf_score, 1),
                "delta": -20.0
            })
        if is_velocity_burst:
            cf_score = max(final_score - 18.0, 0.0)
            counterfactuals.append({
                "scenario": "If transaction velocity anomaly were absent",
                "estimated_risk_score": round(cf_score, 1),
                "delta": -18.0
            })

        return {
            "score": round(final_score, 1),
            "is_flagged": is_flagged,
            "risk_level": risk_level,
            "risk_factors": sorted(factors, key=lambda x: x["points"], reverse=True),
            "counterfactuals": counterfactuals
        }

    def predict(self, transactions: List[Dict], monthly_income_baseline: float = 400000.0) -> List[Tuple[int, float]]:
        """
        Backwards-compatible interface returning List of (is_fraudulent: int, fraud_score: float [0.0 - 1.0]).
        """
        results = []
        for tx in transactions:
            calc = self.calculate_structured_risk(tx, monthly_income_baseline)
            # normalize 0-100 score to 0.0-1.0
            score_norm = min(calc["score"] / 100.0, 0.99)
            is_fraud = 1 if calc["is_flagged"] else 0
            results.append((is_fraud, float(score_norm)))
        return results

fraud_detector = FraudDetector()
