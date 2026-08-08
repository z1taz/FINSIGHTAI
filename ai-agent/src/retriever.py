"""
retriever.py

The RAG layer. Chunks the policy documents in data/policy_docs/, indexes
them with TF-IDF, and retrieves the most relevant chunks for a given
flagged transaction's feature profile.

Deliberately uses TF-IDF instead of a hosted embedding API: the policy
corpus is small and domain-specific (four short documents), and the
whole point of the eval harness downstream is to check whether the
*agent* stays grounded in whatever gets retrieved — that check doesn't
depend on which retrieval method produced the context. Swapping this for
a real embedding index later is a contained change (this module is the
only thing that would need to move).
"""

from __future__ import annotations

import glob
import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    doc_id: str
    heading: str
    text: str


def _split_into_chunks(path: str) -> list[Chunk]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    doc_id = path.split("/")[-1].replace(".md", "")
    sections = re.split(r"\n(?=## )", raw)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"##\s+(.*)", section)
        heading = heading_match.group(1) if heading_match else doc_id
        chunks.append(Chunk(doc_id=doc_id, heading=heading, text=section))
    return chunks


class PolicyRetriever:
    def __init__(self, policy_dir: str = "data/policy_docs"):
        self.chunks: list[Chunk] = []
        for path in sorted(glob.glob(f"{policy_dir}/*.md")):
            self.chunks.extend(_split_into_chunks(path))
        corpus = [c.text for c in self.chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sorted(zip(self.chunks, sims), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def retrieve_for_transaction(self, txn_row: dict, top_k: int = 3) -> list[tuple[Chunk, float]]:
        """Build a query string out of the transaction's risk factors."""
        parts = []
        if not txn_row.get("is_merchant_verified", True):
            parts.append("unverified merchant entity no tax ID LEI")
        mcc = str(txn_row.get("mcc_code", "5999"))
        if mcc in {"7995", "6051", "6012", "0000"}:
            parts.append("high risk merchant category code gambling crypto wire unclassified")
        category = txn_row.get("category", "")
        if category in ["Wire Transfer", "Gambling", "Betting"]:
            parts.append("high risk category label wire transfer gambling betting")
        amount = txn_row.get("amount", 0)
        baseline = txn_row.get("monthly_income_baseline", 400000.0)
        ratio = amount / baseline if baseline else 0
        if ratio >= 0.30:
            parts.append("transaction amount high fraction of monthly income ratio")
        if not parts:
            parts.append("unusual transaction risk factors")
        query = " ".join(parts)
        return self.retrieve(query, top_k=top_k)


if __name__ == "__main__":
    retriever = PolicyRetriever()
    print(f"Indexed {len(retriever.chunks)} chunks from policy docs")
    demo_txn = {
        "is_merchant_verified": False,
        "mcc_code": "0000",
        "category": "Other",
        "amount": 2000,
        "monthly_income_baseline": 400000.0,
    }
    for chunk, score in retriever.retrieve_for_transaction(demo_txn):
        print(f"[{score:.3f}] {chunk.doc_id} :: {chunk.heading}")
