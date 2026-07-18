"""The engine: ties embedding, the vector store, retrieval/synthesis, and eval
into ingest / query / graph operations."""

from __future__ import annotations

from typing import Dict, List

from .corpus import EVAL_SET, SEED_DOCS
from .embeddings import HashingEmbedder
from .evaluate import evaluate
from .rag import answer_query
from .store import VectorStore


def _paragraphs(text: str) -> List[str]:
    """Cheap fallback chunker (blank-line paragraphs) for seeding without Rust."""
    out = []
    for para in text.split("\n\n"):
        cleaned = para.replace("#", "").strip()
        if cleaned:
            out.append(cleaned)
    return out


class Engine:
    def __init__(self, dim: int = 256):
        self.embedder = HashingEmbedder(dim)
        self.store = VectorStore()

    def embed(self, text: str) -> List[float]:
        return self.embedder.embed(text)

    def ingest(self, doc_id: str, action: str, chunks: List[dict] | None = None) -> int:
        if action == "delete":
            return self.store.delete_doc(doc_id)
        chunks = chunks or []
        recs = [(int(c["index"]), c["text"], self.embed(c["text"])) for c in chunks]
        self.store.replace_doc(doc_id, recs)
        return len(recs)

    def ingest_text(self, doc_id: str, text: str) -> int:
        chunks = [{"index": i, "text": t} for i, t in enumerate(_paragraphs(text))]
        return self.ingest(doc_id, "upsert", chunks)

    def query(self, question: str, k: int = 4) -> Dict:
        result = answer_query(self.store, self.embed, question, k)
        ctx_texts = [c["text"] for c in result["contexts"]]
        result["scores"] = evaluate(question, result["answer"], ctx_texts)
        return result

    def graph(self) -> Dict:
        return self.store.graph()

    def seed(self) -> "Engine":
        for doc_id, text in SEED_DOCS.items():
            self.ingest_text(doc_id, text)
        return self

    def eval_suite(self, k: int = 4) -> Dict:
        rows = []
        agg = {"faithfulness": 0.0, "answer_relevance": 0.0,
               "context_precision": 0.0, "context_recall": 0.0}
        for item in EVAL_SET:
            res = self.query(item["question"], k)
            hit_terms = [t for t in item["expect"] if t in res["answer"].lower()]
            rows.append({
                "question": item["question"],
                "answer": res["answer"],
                "expected_hit": len(hit_terms) > 0,
                "scores": res["scores"],
            })
            for key in agg:
                agg[key] += res["scores"][key]
        n = max(len(EVAL_SET), 1)
        mean = {k2: round(v / n, 3) for k2, v in agg.items()}
        answer_hit_rate = round(sum(1 for r in rows if r["expected_hit"]) / n, 3)
        return {"mean_scores": mean, "answer_hit_rate": answer_hit_rate, "rows": rows}
