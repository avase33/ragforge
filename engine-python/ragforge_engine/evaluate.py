"""RAG quality metrics, from scratch (Ragas-style, lexical approximations).

- **context_precision**: fraction of retrieved contexts that share a term with
  the answer (i.e. that actually contributed).
- **context_recall**: fraction of the answer's terms found somewhere in the
  retrieved contexts.
- **faithfulness**: fraction of answer sentences whose terms are mostly
  (>= 50%) covered by the contexts — i.e. not hallucinated.
- **answer_relevance**: fraction of the question's terms reflected in the answer.
"""

from __future__ import annotations

from typing import Dict, List

from .text import sentences, terms


def _terms_set(text: str) -> set:
    return set(terms(text))


def evaluate(question: str, answer: str, contexts: List[str]) -> Dict[str, float]:
    q = _terms_set(question)
    a = _terms_set(answer)
    ctx_term_sets = [_terms_set(c) for c in contexts]
    ctx_union = set().union(*ctx_term_sets) if ctx_term_sets else set()

    # context precision
    if ctx_term_sets:
        relevant = sum(1 for c in ctx_term_sets if a & c)
        context_precision = relevant / len(ctx_term_sets)
    else:
        context_precision = 0.0

    # context recall
    context_recall = (len(a & ctx_union) / len(a)) if a else 0.0

    # faithfulness
    ans_sents = sentences(answer)
    if ans_sents:
        supported = 0
        for s in ans_sents:
            st = _terms_set(s)
            if not st:
                continue
            covered = len(st & ctx_union) / len(st)
            if covered >= 0.5:
                supported += 1
        faithfulness = supported / len(ans_sents)
    else:
        faithfulness = 0.0

    # answer relevance
    answer_relevance = (len(q & a) / len(q)) if q else 0.0

    return {
        "faithfulness": round(faithfulness, 3),
        "answer_relevance": round(answer_relevance, 3),
        "context_precision": round(context_precision, 3),
        "context_recall": round(context_recall, 3),
    }
