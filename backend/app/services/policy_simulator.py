from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, List
from app.models.transaction import Transaction
from app.models.user import User

class PolicySimulatorService:
    """
    Policy Simulation Engine (Section 12).
    Simulates threshold modifications against the dataset and measures
    actual empirical trade-offs: Alerts Generated, Fraud Captured,
    False Positives, and Estimated Investigator Workload.
    """

    async def simulate_policy_change(
        self,
        amount_threshold: float,
        income_ratio_threshold: float,
        flag_unverified_merchants: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        # Fetch transactions
        stmt = select(Transaction, User).join(User, Transaction.user_id == User.id).limit(1000)
        res = await db.execute(stmt)
        rows = res.all()

        total_txs = len(rows)
        alerts_generated = 0
        fraud_captured = 0
        false_positives = 0
        total_fraud_ground_truth = 0

        for tx, user in rows:
            is_actual_fraud = bool(tx.is_fraudulent == 1 or tx.fraud_score >= 65.0)
            if is_actual_fraud:
                total_fraud_ground_truth += 1

            # Evaluate candidate policy
            income_ratio = tx.amount / max(user.monthly_income, 1.0)
            triggers_amount = tx.amount >= amount_threshold
            triggers_income_ratio = income_ratio >= income_ratio_threshold
            triggers_unverified = (not tx.is_merchant_verified) if flag_unverified_merchants else False

            # Policy condition: triggers if (amount OR income ratio) AND (unverified OR high risk category)
            is_alerted = False
            if triggers_amount or triggers_income_ratio:
                if triggers_unverified or tx.category in ["Wire Transfer", "Gambling", "Investment"]:
                    is_alerted = True

            if is_alerted:
                alerts_generated += 1
                if is_actual_fraud:
                    fraud_captured += 1
                else:
                    false_positives += 1

        # Calculate Workload (assume 12 minutes per manual investigation alert)
        investigator_hours = round((alerts_generated * 12.0) / 60.0, 1)
        fraud_catch_rate = round((fraud_captured / total_fraud_ground_truth * 100.0), 1) if total_fraud_ground_truth > 0 else 100.0
        fp_rate = round((false_positives / alerts_generated * 100.0), 1) if alerts_generated > 0 else 0.0

        return {
            "simulation_parameters": {
                "amount_threshold": amount_threshold,
                "income_ratio_threshold": income_ratio_threshold,
                "flag_unverified_merchants": flag_unverified_merchants,
                "dataset_sample_size": total_txs
            },
            "measured_effects": {
                "alerts_generated": alerts_generated,
                "alert_rate_pct": round((alerts_generated / total_txs * 100.0), 1) if total_txs > 0 else 0,
                "fraud_cases_captured": fraud_captured,
                "total_ground_truth_fraud": total_fraud_ground_truth,
                "fraud_catch_rate_pct": fraud_catch_rate,
                "false_positives_generated": false_positives,
                "false_positive_rate_pct": fp_rate,
                "estimated_investigator_workload_hours": investigator_hours,
                "recommended_headcount": max(round(investigator_hours / 7.5, 1), 0.5)
            },
            "trade_off_analysis": (
                f"Setting threshold to ${amount_threshold:,.0f} captures {fraud_catch_rate}% of fraud "
                f"at the cost of {alerts_generated} generated alerts and ~{investigator_hours} hours of investigator queue time."
            )
        }

policy_simulator = PolicySimulatorService()
