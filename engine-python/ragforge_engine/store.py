"""An in-memory vector store keyed by ``doc_id#index``.

Brute-force cosine search — clear and correct, and the interface (upsert /
delete-by-doc / search) is exactly what a Qdrant/Milvus adapter would implement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .embeddings import cosine


@dataclass
class Record:
    id: str
    doc_id: str
    index: int
    text: str
    vec: List[float] = field(default_factory=list)


class VectorStore:
    def __init__(self):
        self._records: Dict[str, Record] = {}

    def upsert(self, doc_id: str, index: int, text: str, vec: List[float]) -> None:
        rid = f"{doc_id}#{index}"
        self._records[rid] = Record(id=rid, doc_id=doc_id, index=index, text=text, vec=vec)

    def delete_doc(self, doc_id: str) -> int:
        ids = [rid for rid, r in self._records.items() if r.doc_id == doc_id]
        for rid in ids:
            del self._records[rid]
        return len(ids)

    def replace_doc(self, doc_id: str, chunks: List[Tuple[int, str, List[float]]]) -> None:
        """Atomically swap all chunks for a doc (upsert semantics)."""
        self.delete_doc(doc_id)
        for index, text, vec in chunks:
            self.upsert(doc_id, index, text, vec)

    def search(self, qvec: List[float], k: int = 4) -> List[Tuple[Record, float]]:
        scored = [(r, cosine(qvec, r.vec)) for r in self._records.values()]
        scored.sort(key=lambda rs: rs[1], reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        return len(self._records)

    def docs(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self._records.values():
            counts[r.doc_id] = counts.get(r.doc_id, 0) + 1
        return counts

    def graph(self) -> dict:
        counts = self.docs()
        docs = [{"doc_id": d, "chunks": n, "stale": False} for d, n in sorted(counts.items())]
        edges = [
            {"from": r.doc_id, "to": r.id}
            for r in sorted(self._records.values(), key=lambda x: x.id)
        ]
        return {"docs": docs, "edges": edges}
