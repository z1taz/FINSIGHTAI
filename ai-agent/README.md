# FinSight AI: Fraud Explainer Agent + Eval Harness

An agent that explains *why* [FinSightAI](https://github.com/z1taz/FinSightAI)'s
fraud detector flagged a transaction, grounded in retrieved policy
documents (RAG), plus an eval harness that checks whether the agent's
explanations are actually trustworthy — not just plausible-sounding.

**This is a direct extension of a real system**, not a lookalike built
for a portfolio. `src/detector.py` is a port of the actual detection
logic in `FinSightAI/backend/app/services/fraud_detector.py` — same MCC
risk map, same category risk map, same weighted risk-scoring formula
(unverified merchant +0.40, high-risk MCC +0.35, risky category +0.15,
income-ratio tiers up to +0.25, flag threshold 0.50, blended 70/30 with
an Isolation Forest score). Everything built on top — the RAG layer,
the agent, the eval harness — is new work, explaining the real system's
real decisions.

## Why this exists

FinSightAI's detector can tell you a transaction crossed the 0.50 risk
threshold. It can't tell an analyst *which* factors combined to get
there, in language they can act on. An LLM can write that explanation —
but an LLM confidently explaining a flag using a factor that wasn't
actually present is worse than no explanation at all. That's the actual
engineering problem here: not "can an agent explain a fraud flag," but
"can I verify it only explains what it can actually support, and
abstains when it can't."

That question matters more than usual for this specific detector,
because its whole design principle is that **no single factor should
flag a transaction** — it takes two or more combining past 0.50. A
naive explainer agent, told "the merchant was unverified," will happily
write a confident paragraph about fraud even when that's the *only*
factor present and the real system wouldn't have flagged it at all.
The eval harness exists specifically to catch that failure mode.

## Architecture

```
transactions.csv  (schema matches FinSightAI's Transaction model:
      |             amount, category, merchant, mcc_code, is_merchant_verified)
      v
  [detector.py]  Ported FinSightAI risk scoring: rule-based weighted
      |          score (merchant verification, MCC risk, category risk,
      |          income ratio) blended with an Isolation Forest score
      v
  flagged transactions + rule_risk_score
      |
      v
  [retriever.py]  TF-IDF retrieval over data/policy_docs/*.md
      |            (4 docs, one per real risk factor, chunked by section)
      v
  retrieved policy evidence
      |
      v
  [agent.py]  Builds a grounded prompt (profile + evidence only),
      |       calls the LLM, or abstains if evidence is weak
      v
  AgentOutput (explanation + which chunks were used + abstain flag)
      |
      v
  [eval_harness.py]  Runs the agent over eval/eval_set.jsonl and checks:
                        - grounding: every cited policy ID must appear
                          in the retrieved chunks (else: hallucinated
                          citation)
                        - coverage: for clear multi-factor cases, did it
                          cite at least one of the genuinely-applicable
                          policies?
                        - abstention: for single-factor cases (true but
                          below the real 0.50 threshold), did it
                          correctly decline instead of guessing?
```

## Quickstart

```bash
pip install -r requirements.txt

# 1. Generate synthetic transaction data matching FinSightAI's schema
python src/generate_data.py

# 2. Run the ported detector, flag anomalies
python src/detector.py

# 3. Build the labeled eval set (pulls real flagged cases + hand-built
#    single-factor cases for abstention testing)
python -m src.build_eval_set

# 4. Single-transaction demo, plumbing visible at every stage
python scripts/run_demo.py

# 5. Full eval harness — the main deliverable
export ANTHROPIC_API_KEY=sk-...   # omit this to see the offline fallback path
python -m src.eval_harness
```

Every stage runs without `ANTHROPIC_API_KEY` set — the agent falls back
to a clearly-labeled offline stub so the pipeline is inspectable end to
end. Set the key to see real model output; the eval harness explicitly
flags which mode it ran in so the two are never confused in the report.

## What the eval harness actually measures

Three clear cases, pulled from real detector output, where 2-3 real
risk factors combine (e.g. an unverified merchant at an unclassified
MCC gateway — both MV-01 and MCC-02 genuinely apply). Four hand-built
single-factor cases, each hitting exactly one real risk factor at a
value that's individually true but stays under the 0.50 flag threshold
on its own — the correct behavior is to abstain, not force an
explanation.

- **Grounding rate** — fraction of cases with zero hallucinated policy
  citations.
- **Coverage rate** — on clear cases, did it cite at least one policy
  that's genuinely applicable (not every applicable one — see
  `build_eval_set.py`'s docstring for why that's the right bar here).
- **Abstention accuracy** — on single-factor cases, did it correctly
  decline; on clear multi-factor cases, did it correctly *not* decline.

## A real bug this project caught

While wiring the detector to the real transactions.csv, `mcc_code`
values like `"0000"` silently became the integer `0` on CSV round-trip
via `pandas.read_csv`, which broke the high-risk-MCC check entirely —
every unverified-merchant-at-an-unclassified-gateway case failed to
flag. Fixed with an explicit `dtype={"mcc_code": str}` on every read.
Left the fix visible in `detector.py` with a comment rather than
quietly correcting it, since it's a legitimate example of the kind of
bug that a systems-level eval (checking end-to-end behavior, not just
unit-testing one function) is supposed to surface.

## What I'd build next with more time

- Swap the TF-IDF retriever for a real embedding index once the policy
  corpus grows past a size where lexical overlap stops being a reliable
  proxy for relevance.
- Add an LLM-as-judge scoring pass (behind the same API-key gate) for
  explanation *clarity*, which the current harness doesn't touch — it
  only checks grounding and abstention, both of which are checkable
  without asking a model to grade another model.
- Wire this directly into FinSightAI's FastAPI backend as a new
  `/analytics/explain/{txn_id}` endpoint, so explanations show up in the
  actual Anomalies dashboard instead of living in a separate repo.
