"""
run_demo.py

End-to-end walkthrough on one transaction: detector flags it -> retriever
pulls policy evidence -> agent explains it. Prints each stage so the
pipeline is legible, not just the final answer.

Usage:
    python scripts/run_demo.py                 # picks the top-flagged txn
    python scripts/run_demo.py --txn-id T017509 # a specific one
    ANTHROPIC_API_KEY=sk-... python scripts/run_demo.py   # live model
"""

import argparse
import sys

sys.path.insert(0, ".")

import pandas as pd

from src.agent import FraudExplainerAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--txn-id", default=None, help="Specific flagged txn_id to explain")
    parser.add_argument(
        "--scored-path", default="reports/sample_flagged.csv",
        help="Output of `python src/detector.py`",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.scored_path, dtype={"mcc_code": str})
    if args.txn_id:
        row = df[df["txn_id"] == args.txn_id].iloc[0]
    else:
        row = df.iloc[0]  # highest fraud score

    print("=" * 70)
    print("STAGE 1 — Detector output")
    print("=" * 70)
    print(f"txn_id:                {row['txn_id']}")
    print(f"account_id:            {row['account_id']}")
    print(f"fraud_score:           {row['fraud_score']:.3f}")
    print(f"rule_risk_score:       {row['rule_risk_score']:.2f}")
    print(f"amount:                {row['amount']:.2f}")
    print(f"is_merchant_verified:  {row['is_merchant_verified']}")
    print(f"mcc_code:              {row['mcc_code']}")
    print(f"category:              {row['category']}")
    print(f"(ground truth, not shown to the agent) fraud_type: {row.get('fraud_type', 'n/a')}")

    agent = FraudExplainerAgent()

    print("\n" + "=" * 70)
    print("STAGE 2 — RAG retrieval + agent explanation")
    print("=" * 70)
    output = agent.explain(row.to_dict())

    print(f"\nRetrieved {len(output.retrieved_chunks)} policy chunks:")
    for chunk in output.retrieved_chunks:
        print(f"  - {chunk.doc_id} :: {chunk.heading}")

    print(f"\nModel: {output.llm_response.model} (live={output.llm_response.live})")
    print(f"Latency: {output.llm_response.latency_s:.2f}s")
    print(f"Abstained: {output.abstained}")
    print("\nExplanation:")
    print(output.explanation)


if __name__ == "__main__":
    main()
