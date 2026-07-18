"""A from-scratch hashing (feature-hashing) text embedder.

No numpy, no sentence-transformers. Each term is hashed to a bucket (the
"hashing trick") with a second hash bit giving a +/- sign to reduce collisions,
weighted by sublinear term frequency ``1 + log(tf)``. The vector is L2
normalised so cosine similarity is a dot product. Deterministic across runs
because it uses ``hashlib`` rather than Python's salted ``hash()``.
"""

from __future__ import annotations

import hashlib
import math
from typing import Dict, List

from .text import terms


def _h(term: str) -> int:
    return int.from_bytes(hashlib.md5(term.encode()).digest()[:8], "big")


class HashingEmbedder:
    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        tf: Dict[str, int] = {}
        for t in terms(text):
            tf[t] = tf.get(t, 0) + 1

        vec = [0.0] * self.dim
        for term, count in tf.items():
            h = _h(term)
            idx = h % self.dim
            sign = 1.0 if (h >> 33) & 1 == 0 else -1.0
            vec[idx] += sign * (1.0 + math.log(count))

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


def cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
