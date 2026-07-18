"""ragforge engine: from-scratch embeddings, vector store, RAG, and eval."""

from .embeddings import HashingEmbedder
from .store import VectorStore
from .engine import Engine

__all__ = ["HashingEmbedder", "VectorStore", "Engine"]
__version__ = "0.1.0"
