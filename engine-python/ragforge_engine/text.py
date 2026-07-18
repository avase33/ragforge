"""Shared tokenisation helpers (stable, dependency-free)."""

from __future__ import annotations

import re
from typing import List

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "this", "that", "these",
    "those", "as", "at", "by", "from", "we", "you", "they", "i", "he", "she",
    "his", "her", "its", "our", "your", "their", "will", "can", "do", "does",
    "if", "then", "so", "not", "no", "yes", "have", "has", "had", "how", "what",
    "when", "where", "which", "who", "into", "out", "up", "down", "over", "my",
    "me", "us", "them", "about", "there", "here",
}

_WORD = re.compile(r"[a-z0-9]+")
_SENT = re.compile(r"[^.!?]+[.!?]?")


def terms(text: str) -> List[str]:
    """Content terms: lowercased words, stopwords and 1-char tokens removed."""
    return [w for w in _WORD.findall(text.lower()) if len(w) >= 2 and w not in STOPWORDS]


def sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT.findall(text) if s.strip()]
