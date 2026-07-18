"""Retrieval + extractive synthesis.

Offline the "LLM" is an honest extractive synthesizer: it ranks sentences from
the retrieved chunks by overlap with the question and stitches the best ones
into an answer. Set ``RAGFORGE_LLM=openai`` to route synthesis to a real model.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from .store import Record, VectorStore
from .text import sentences, terms


def _overlap(a_terms: set, b_terms: set) -> int:
    return len(a_terms & b_terms)


def synthesize(question: str, contexts: List[Record], max_sentences: int = 3) -> str:
    q = set(terms(question))
    scored: List[Tuple[float, str]] = []
    for rec in contexts:
        for sent in sentences(rec.text):
            s_terms = set(terms(sent))
            if not s_terms:
                continue
            score = _overlap(q, s_terms) / (len(q) + 1e-9)
            if score > 0:
                scored.append((score, sent))
    if not scored:
        return "I don't have information on that in the indexed documents."

    scored.sort(key=lambda x: x[0], reverse=True)
    picked: List[str] = []
    seen = set()
    for _, sent in scored:
        key = sent.lower()
        if key in seen:
            continue
        seen.add(key)
        picked.append(sent)
        if len(picked) >= max_sentences:
            break
    return " ".join(picked)


def answer_query(
    store: VectorStore, embed, question: str, k: int = 4
) -> Dict:
    qvec = embed(question)
    hits = store.search(qvec, k)
    contexts = [rec for rec, _ in hits]

    if os.getenv("RAGFORGE_LLM") == "openai":
        try:
            from .real import synthesize_openai

            answer = synthesize_openai(question, contexts)
        except Exception:
            answer = synthesize(question, contexts)
    else:
        answer = synthesize(question, contexts)

    return {
        "answer": answer,
        "contexts": [
            {"id": rec.id, "text": rec.text, "score": round(score, 4)}
            for rec, score in hits
        ],
    }
