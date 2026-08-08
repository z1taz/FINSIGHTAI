"""
eval_harness.py

Runs the agent over every case in eval/eval_set.jsonl and scores it on
three axes that matter more than "does it sound plausible":

1. grounding — every policy ID the agent cites must appear in the chunks
   it was actually given. A cited ID that ISN'T in the retrieved context
   is a hallucinated citation: the agent claimed support that doesn't
   exist. This is checked with a regex, not an LLM judge — it's a fact
   about strings, not a matter of opinion.

2. coverage — for non-ambiguous cases, did the agent cite the policy ID
   that actually explains the flag? Citing the wrong-but-real policy is
   graded separately from citing a fabricated one: it's a retrieval/
   reasoning miss, not a hallucination.

3. abstention correctness — for cases built to be ambiguous, did the
   agent correctly decline to give a confident explanation? Answering
   confidently on a case designed to be borderline is scored as a
   "confident wrong answer" — the failure mode the whole harness exists
   to catch.

Run with `python -m src.eval_harness`. Works with or without
ANTHROPIC_API_KEY set (see llm_client.py) — without a key every case
will show up as "not graded (offline fallback)" so the report still
distinguishes "the pipeline works" from "the model output is good,"
which are two different claims.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

from src.agent import FraudExplainerAgent, AgentOutput

CITED_POLICY_RE = re.compile(r"\b([A-Z]{2,4}-\d{2})\b")


@dataclass
class CaseResult:
    txn_id: str
    should_abstain: bool
    expected_policy_ids: list[str] | None
    abstained: bool
    cited_policy_ids: list[str]
    retrieved_policy_ids: list[str]
    hallucinated_citations: list[str]
    grounded: bool
    coverage_hit: bool | None  # None when not applicable (ambiguous case)
    abstention_correct: bool
    live_model: bool
    latency_s: float
    explanation: str


def _extract_cited_policy_ids(text: str) -> list[str]:
    return sorted(set(CITED_POLICY_RE.findall(text)))


def _extract_retrieved_policy_ids(output: AgentOutput) -> list[str]:
    ids = []
    for chunk in output.retrieved_chunks:
        match = CITED_POLICY_RE.search(chunk.text)
        if match:
            ids.append(match.group(1))
    return sorted(set(ids))


def score_case(case: dict, output: AgentOutput) -> CaseResult:
    cited = _extract_cited_policy_ids(output.explanation)
    retrieved = _extract_retrieved_policy_ids(output)
    hallucinated = [pid for pid in cited if pid not in retrieved]
    grounded = len(hallucinated) == 0

    # expected_policy_id in the eval case may be a list (a clear case can
    # legitimately support more than one real policy) or None (ambiguous
    # case, nothing should be confidently cited). Coverage only requires
    # citing at least one genuinely-applicable policy, not all of them —
    # see build_eval_set.py's module docstring for why.
    expected = case["expected_policy_id"]
    if isinstance(expected, str):
        expected = [expected]

    if case["should_abstain"]:
        coverage_hit = None
    else:
        coverage_hit = (
            any(pid in cited for pid in (expected or [])) if not output.abstained else False
        )

    if case["should_abstain"]:
        abstention_correct = output.abstained
    else:
        abstention_correct = not output.abstained

    return CaseResult(
        txn_id=case["txn_id"],
        should_abstain=case["should_abstain"],
        expected_policy_ids=expected,
        abstained=output.abstained,
        cited_policy_ids=cited,
        retrieved_policy_ids=retrieved,
        hallucinated_citations=hallucinated,
        grounded=grounded,
        coverage_hit=coverage_hit,
        abstention_correct=abstention_correct,
        live_model=output.llm_response.live,
        latency_s=output.llm_response.latency_s,
        explanation=output.explanation,
    )


def run_harness(eval_path: str = "eval/eval_set.jsonl") -> list[CaseResult]:
    agent = FraudExplainerAgent()
    results = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            case = json.loads(line)
            output = agent.explain(case["profile"])
            results.append(score_case(case, output))
    return results


def summarize(results: list[CaseResult]) -> dict:
    n = len(results)
    live_results = [r for r in results if r.live_model]
    non_ambiguous = [r for r in results if not r.should_abstain]
    ambiguous = [r for r in results if r.should_abstain]

    summary = {
        "total_cases": n,
        "live_model_cases": len(live_results),
        "offline_fallback_cases": n - len(live_results),
        "grounding_rate": round(sum(r.grounded for r in results) / n, 3),
        "hallucinated_citation_count": sum(len(r.hallucinated_citations) for r in results),
        "coverage_rate_non_ambiguous": (
            round(sum(bool(r.coverage_hit) for r in non_ambiguous) / len(non_ambiguous), 3)
            if non_ambiguous
            else None
        ),
        "abstention_accuracy_ambiguous": (
            round(sum(r.abstention_correct for r in ambiguous) / len(ambiguous), 3)
            if ambiguous
            else None
        ),
        "overall_abstention_accuracy": round(sum(r.abstention_correct for r in results) / n, 3),
        "mean_latency_s": round(sum(r.latency_s for r in results) / n, 4),
    }
    return summary


def write_report(results: list[CaseResult], summary: dict, out_path: str = "reports/eval_report.json"):
    payload = {"summary": summary, "cases": [asdict(r) for r in results]}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_path


def print_report(results: list[CaseResult], summary: dict):
    print("=" * 70)
    print("EVAL HARNESS REPORT")
    print("=" * 70)
    if summary["offline_fallback_cases"] > 0:
        print(
            f"NOTE: {summary['offline_fallback_cases']}/{summary['total_cases']} cases ran "
            f"in OFFLINE FALLBACK mode (no ANTHROPIC_API_KEY set). Grounding/coverage/"
            f"abstention numbers below are NOT meaningful for those cases — set the key "
            f"for a real run.\n"
        )
    for k, v in summary.items():
        print(f"{k:35s}: {v}")
    print("-" * 70)
    for r in results:
        flag = "OK" if r.abstention_correct and r.grounded else "CHECK"
        live_tag = "live" if r.live_model else "offline"
        print(
            f"[{flag:5s}][{live_tag:7s}] {r.txn_id:35s} "
            f"abstained={r.abstained!s:5s} expected={str(r.expected_policy_ids):20s} "
            f"cited={r.cited_policy_ids} hallucinated={r.hallucinated_citations}"
        )


if __name__ == "__main__":
    results = run_harness()
    summary = summarize(results)
    print_report(results, summary)
    path = write_report(results, summary)
    print(f"\nFull report written to {path}")
