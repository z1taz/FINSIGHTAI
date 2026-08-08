"""
agent.py

The agent. Given a flagged transaction (output of detector.py), it:
  1. Retrieves the most relevant policy chunks (retriever.py).
  2. Builds a prompt that gives the model ONLY the transaction's feature
     profile and the retrieved policy text as evidence.
  3. Calls the LLM (llm_client.py) and asks it to either (a) explain the
     flag citing specific policy IDs, or (b) abstain if the retrieved
     evidence doesn't clearly support any policy.

The abstain option is deliberate and load-bearing, not decoration. A
fraud analyst acting on a confidently-wrong explanation is worse than
one that says "insufficient evidence" and routes to a human. The eval
harness (eval_harness.py) specifically tests whether the agent respects
this on cases built to be ambiguous.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.llm_client import call_llm, LLMResponse
from src.retriever import PolicyRetriever, Chunk

SYSTEM_PROMPT = """You are a fraud-review assistant. You explain why a transaction \
was flagged, for a human analyst who will make the final call.

Rules you must follow:
1. Only cite policy IDs (e.g. "MV-01", "MCC-02") that appear in the evidence \
provided below. Never invent a policy ID or cite one not shown to you.
2. Only state feature values (merchant verification, MCC code, category, \
income ratio, amount) that are given to you in the transaction profile. \
Never invent numbers.
3. If the evidence does not clearly support any single policy, or if only \
one weak risk factor is present without enough combined weight to explain \
a flag, say so explicitly and respond with "ABSTAIN: insufficient evidence" \
followed by a one-line reason. Do not guess at a plausible-sounding \
explanation.
4. Keep the explanation to 3-4 sentences, written for a human analyst who \
will decide whether to escalate, not for a customer."""


@dataclass
class AgentOutput:
    txn_id: str
    explanation: str
    retrieved_chunks: list[Chunk]
    llm_response: LLMResponse
    abstained: bool = field(init=False)

    def __post_init__(self):
        self.abstained = self.explanation.strip().upper().startswith("ABSTAIN")


def _format_transaction_profile(txn_row: dict) -> str:
    amount = txn_row.get("amount", 0)
    baseline = txn_row.get("monthly_income_baseline", 400000.0)
    ratio = amount / baseline if baseline else 0
    return (
        f"- is_merchant_verified: {txn_row.get('is_merchant_verified')}\n"
        f"- mcc_code: {txn_row.get('mcc_code')}\n"
        f"- category: {txn_row.get('category')}\n"
        f"- amount: {round(amount, 2)}\n"
        f"- monthly_income_baseline: {round(baseline, 2)}\n"
        f"- income_ratio: {round(ratio, 3)}\n"
        f"- rule_risk_score (if provided by detector): {txn_row.get('rule_risk_score', 'n/a')}"
    )


def _format_evidence(chunks: list[tuple[Chunk, float]]) -> str:
    blocks = []
    for chunk, score in chunks:
        policy_id_match = re.search(r"([A-Z]{2,4}-\d{2})", chunk.text)
        policy_id = policy_id_match.group(1) if policy_id_match else chunk.doc_id
        blocks.append(f"[{policy_id} | relevance {score:.2f}]\n{chunk.text}")
    return "\n\n".join(blocks)


class FraudExplainerAgent:
    def __init__(self, retriever: PolicyRetriever | None = None):
        self.retriever = retriever or PolicyRetriever()

    def explain(self, txn_row: dict, top_k: int = 3) -> AgentOutput:
        retrieved = self.retriever.retrieve_for_transaction(txn_row, top_k=top_k)
        evidence_text = _format_evidence(retrieved)
        profile_text = _format_transaction_profile(txn_row)

        prompt = (
            f"Transaction profile:\n{profile_text}\n\n"
            f"Retrieved policy evidence:\n{evidence_text}\n\n"
            "Explain why this transaction was flagged, or abstain per the rules."
        )

        response = call_llm(prompt, system=SYSTEM_PROMPT)
        return AgentOutput(
            txn_id=txn_row.get("txn_id", "unknown"),
            explanation=response.text,
            retrieved_chunks=[c for c, _ in retrieved],
            llm_response=response,
        )


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("reports/sample_flagged.csv", dtype={"mcc_code": str})
    agent = FraudExplainerAgent()
    row = df.iloc[0].to_dict()
    output = agent.explain(row)
    print(f"txn_id: {output.txn_id}")
    print(f"live model call: {output.llm_response.live}")
    print(f"abstained: {output.abstained}")
    print("---")
    print(output.explanation)
