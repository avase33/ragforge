"""FastAPI vector engine: /ingest, /query, /eval, /graph.

Seeds built-in corporate docs at startup so the API is useful immediately, even
before the Go crawler pushes anything.
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from .engine import Engine

app = FastAPI(title="ragforge engine", version="0.1.0")
_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine().seed()
    return _engine


class Chunk(BaseModel):
    index: int = 0
    text: str = ""


class IngestRequest(BaseModel):
    doc_id: str
    action: str = "upsert"
    chunks: List[Chunk] = []


class QueryRequest(BaseModel):
    question: str
    k: int = 4


@app.on_event("startup")
def _warm() -> None:
    get_engine()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "vectors": len(get_engine().store)}


@app.post("/ingest")
def ingest(req: IngestRequest) -> Dict:
    n = get_engine().ingest(
        req.doc_id, req.action, [c.model_dump() for c in req.chunks]
    )
    return {"doc_id": req.doc_id, "action": req.action, "chunks": n}


@app.post("/query")
def query(req: QueryRequest) -> Dict:
    return get_engine().query(req.question, req.k)


@app.get("/eval")
def eval_ep() -> Dict:
    return get_engine().eval_suite()


@app.get("/graph")
def graph() -> Dict:
    return get_engine().graph()
