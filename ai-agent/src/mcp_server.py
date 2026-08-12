"""
mcp_server.py

Exposes FinSight AI's fraud-detection pipeline as an MCP (Model Context
Protocol) server, so any MCP-compatible client — Claude Desktop, another
agent, a different codebase entirely — can call it through the standard
protocol instead of importing these modules directly.

This does NOT reimplement the detection or explanation logic. It imports
and calls the same FraudDetector (detector.py) and FraudExplainerAgent
(agent.py) that the eval harness tests. The MCP layer is a thin,
protocol-compliant wrapper around real, already-tested logic.

Two tools are exposed:
  - check_transaction: runs the real rule-based fraud score on a single
      transaction (no historical data needed — an unfitted FraudDetector
          falls back to pure rule-based scoring, which is exactly the
              deterministic, explainable path this tool should expose).
                - explain_flag: runs the RAG-grounded explainer agent on a flagged
                    transaction, returning a grounded explanation or an explicit
                        abstention, identical to what the eval harness measures.

                        Run it:
                            python -m src.mcp_server

                            Connect it to Claude Desktop by adding this to claude_desktop_config.json:
                                {
                                      "mcpServers": {
                                              "finsight-fraud": {
                                                        "command": "python",
                                                                  "args": ["-m", "src.mcp_server"],
                                                                            "cwd": "/absolute/path/to/ai-agent"
        }
              }
                  }
                  """

from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

from src.agent import FraudExplainerAgent
from src.detector import FraudDetector

mcp = FastMCP("finsight-fraud-detection")

_agent = FraudExplainerAgent()

# --- Simple in-memory cache for explain_flag -------------------------------
# Explaining the same transaction twice re-runs retrieval + an LLM call for
# no reason — the evidence and the answer don't change. This cache keys on
# the transaction's actual risk-relevant fields (not object identity), so
# two calls describing the same transaction hit the cache even if they come
# from different clients or sessions.
_explain_cache: dict[str, dict[str, Any]] = {}


def _cache_key(txn: dict[str, Any]) -> str:
      relevant = {
                "amount": txn.get("amount"),
                "monthly_income_baseline": txn.get("monthly_income_baseline", 400000.0),
                "is_merchant_verified": txn.get("is_merchant_verified"),
                "mcc_code": str(txn.get("mcc_code")),
                "category": txn.get("category"),
      }
      return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()


@mcp.tool()
def check_transaction(
      amount: float,
      is_merchant_verified: bool,
      mcc_code: str,
      category: str,
      monthly_income_baseline: float = 400000.0,
      txn_id: str = "adhoc",
) -> dict:
      """Score a single transaction using FinSight's real rule-based fraud detector.

          Runs the same weighted risk-scoring formula as the production backend:
              unverified merchant (+0.40), high-risk MCC (+0.35), high-risk category
                  (+0.15), and income-ratio scaling — flagged at a combined score >= 0.50.

                      Args:
                              amount: Transaction amount.
                                      is_merchant_verified: Whether the merchant has a verified entity record.
                                              mcc_code: ISO merchant category code, e.g. "0000", "7995", "5411".
                                                      category: Transaction category label, e.g. "Other", "Wire Transfer".
                                                              monthly_income_baseline: Account holder's monthly income baseline,
                                                                          used to compute the income-ratio risk factor. Defaults to the
                                                                                      same 400000 fallback the FinSight frontend uses.
                                                                                              txn_id: Optional identifier for the transaction, for traceability.

                                                                                                  Returns:
                                                                                                          A dict with fraud_score, flagged (bool), rule_risk_score, and the
                                                                                                                  original input fields, matching the shape detector.py produces.
                                                                                                                      """
      row = pd.DataFrame([{
          "txn_id": txn_id,
          "amount": amount,
          "monthly_income_baseline": monthly_income_baseline,
          "is_merchant_verified": is_merchant_verified,
          "mcc_code": str(mcc_code),
          "category": category,
      }])

    # Unfitted FraudDetector: self.model is None, so score() takes the pure
      # rule-based path for anything below threshold too — no historical data
    # needed, and it's the deterministic path this tool is meant to expose.
    scored = FraudDetector().score(row)
    result = scored.iloc[0].to_dict()

    return {
              "txn_id": result["txn_id"],
              "fraud_score": round(float(result["fraud_score"]), 4),
              "flagged": bool(result["flagged"]),
              "rule_risk_score": round(float(result["rule_risk_score"]), 4),
              "amount": amount,
              "is_merchant_verified": is_merchant_verified,
              "mcc_code": str(mcc_code),
              "category": category,
    }


@mcp.tool()
def explain_flag(
      txn_id: str,
      amount: float,
      is_merchant_verified: bool,
      mcc_code: str,
      category: str,
      monthly_income_baseline: float = 400000.0,
) -> dict:
      """Explain why a transaction was flagged, grounded in retrieved policy text.

          Runs the same RAG-grounded FraudExplainerAgent the eval harness scores
              for grounding, coverage, and abstention. The agent will explicitly
                  abstain ("ABSTAIN: insufficient evidence") rather than guess when the
                      retrieved policy evidence doesn't clearly support a flag — that is
                          correct behavior, not a failure, and callers should treat an abstained
                              response as "route to a human," not as an error.

                                  Args:
                                          txn_id: Transaction identifier.
                                                  amount: Transaction amount.
                                                          is_merchant_verified: Whether the merchant has a verified entity record.
                                                                  mcc_code: ISO merchant category code.
                                                                          category: Transaction category label.
                                                                                  monthly_income_baseline: Account holder's monthly income baseline.

                                                                                      Returns:
                                                                                              A dict with explanation (str), abstained (bool), cited_policy_ids
                                                                                                      (list[str]), and cache_hit (bool) indicating whether this exact
                                                                                                              transaction was already explained in this server's lifetime.
                                                                                                                  """
      txn_row = {
          "txn_id": txn_id,
          "amount": amount,
          "monthly_income_baseline": monthly_income_baseline,
          "is_merchant_verified": is_merchant_verified,
          "mcc_code": str(mcc_code),
          "category": category,
      }

    key = _cache_key(txn_row)
    if key in _explain_cache:
              cached = dict(_explain_cache[key])
              cached["cache_hit"] = True
              return cached

    output = _agent.explain(txn_row)

    cited_ids = []
    for chunk in output.retrieved_chunks:
              cited_ids.append(chunk.doc_id)

    result = {
              "txn_id": output.txn_id,
              "explanation": output.explanation,
              "abstained": output.abstained,
              "cited_policy_ids": cited_ids,
              "cache_hit": False,
    }
    _explain_cache[key] = result
    return result


if __name__ == "__main__":
      mcp.run()
  
