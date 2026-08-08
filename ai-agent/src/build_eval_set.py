"""
build_eval_set.py

Builds eval/eval_set.jsonl against the REAL FinSightAI scoring logic
(ported in detector.py): a transaction only flags when 2+ independent
risk factors combine to clear a 0.50 score. That design is exactly what
makes the ambiguous cases below meaningful — each one hits exactly ONE
real risk factor, individually true and individually insufficient. A
good agent explanation should abstain on these; a bad one will notice
"unverified merchant = true" and confidently explain a flag that the
actual system wouldn't even raise.

Clear cases are pulled from real detector.py output (multi-factor fraud
types actually injected by generate_data.py). Each clear case may
legitimately support more than one policy — e.g. an unverified merchant
at a high-risk MCC supports both MV-01 and MCC-02 — so
`expected_policy_ids` is a list, and coverage only requires the agent
cite at least one of the genuinely-applicable policies, not all of them.
"""

import json

import pandas as pd

# (fraud_type in generate_data.py, [policy IDs genuinely supported by that pattern])
CLEAR_CASE_SPECS = [
    ("unverified_high_risk_mcc", ["MV-01", "MCC-02"]),
    ("high_income_ratio_wire", ["MCC-02", "CAT-03", "INC-04"]),
    ("gambling_mcc", ["MCC-02", "CAT-03"]),
]

# Each hits exactly one real risk factor — individually true, individually
# below the 0.50 flag threshold. Correct agent behavior: abstain.
AMBIGUOUS_CASES = [
    {
        "txn_id": "AMBIG-unverified-only",
        "note": "Unverified merchant (+0.40) only — low-risk MCC, low-risk category, low income ratio. Total 0.40 < 0.50.",
        "is_merchant_verified": False,
        "mcc_code": "5411",
        "category": "Groceries",
        "amount": 900,
        "monthly_income_baseline": 400000.0,
    },
    {
        "txn_id": "AMBIG-mcc-only",
        "note": "High-risk MCC (+0.35) only — verified merchant, category label not in the risky set, low income ratio. Total 0.35 < 0.50.",
        "is_merchant_verified": True,
        "mcc_code": "6051",
        "category": "Investment",
        "amount": 5000,
        "monthly_income_baseline": 400000.0,
    },
    {
        "txn_id": "AMBIG-category-only",
        "note": "Risky category label (+0.15) only — verified merchant, low-risk MCC, low income ratio. Total 0.15 < 0.50.",
        "is_merchant_verified": True,
        "mcc_code": "5999",
        "category": "Wire Transfer",
        "amount": 1200,
        "monthly_income_baseline": 400000.0,
    },
    {
        "txn_id": "AMBIG-income-ratio-only",
        "note": "Income ratio in the 0.30-0.50 tier (+0.08) only — verified merchant, low-risk MCC/category. Total 0.08 < 0.50.",
        "is_merchant_verified": True,
        "mcc_code": "5311",
        "category": "Shopping",
        "amount": 140000,
        "monthly_income_baseline": 400000.0,
    },
]


def build_eval_set(
    scored_path: str = "reports/sample_flagged.csv",
    out_path: str = "eval/eval_set.jsonl",
):
    df = pd.read_csv(scored_path, dtype={"mcc_code": str})
    cases = []

    for fraud_type, policy_ids in CLEAR_CASE_SPECS:
        matches = df[df["fraud_type"] == fraud_type]
        if matches.empty:
            print(f"WARNING: detector did not flag any real '{fraud_type}' case — skipping.")
            continue
        row = matches.iloc[0]
        profile = {
            "txn_id": row["txn_id"],
            "is_merchant_verified": bool(row["is_merchant_verified"]),
            "mcc_code": str(row["mcc_code"]),
            "category": row["category"],
            "amount": float(row["amount"]),
            "monthly_income_baseline": float(row["monthly_income_baseline"]),
            "rule_risk_score": float(row["rule_risk_score"]),
        }
        cases.append(
            {
                "txn_id": row["txn_id"],
                "profile": profile,
                "expected_policy_id": policy_ids,
                "should_abstain": False,
                "note": f"Clear {fraud_type} case pulled from real detector output.",
            }
        )

    for case in AMBIGUOUS_CASES:
        case = dict(case)
        note = case.pop("note")
        txn_id = case["txn_id"]
        cases.append(
            {
                "txn_id": txn_id,
                "profile": case,
                "expected_policy_id": None,
                "should_abstain": True,
                "note": note,
            }
        )

    with open(out_path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")

    print(
        f"Wrote {len(cases)} eval cases to {out_path} "
        f"({len(CLEAR_CASE_SPECS)} clear, {len(AMBIGUOUS_CASES)} ambiguous)"
    )


if __name__ == "__main__":
    build_eval_set()
