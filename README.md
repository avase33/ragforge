# ragforge 🗄️

**An autonomous vector data engine for continuous RAG.** A Go crawler watches
document sources and detects changes, a Rust service splits text at **topic
shifts** rather than arbitrary token counts, and a from-scratch Python engine
embeds, indexes, retrieves, synthesizes, and **grades its own answers** — so
your agents' knowledge base never goes stale.

Four languages, each on the layer it's built for, over one JSON protocol:

```
sources ─▶ Go crawler ─▶ Rust chunker ─▶ Python engine ─▶ vector store
           │ (watch+webhook) (topic-shift)  (embed+index)      │
           └────────────── TS dashboard ◀── /query /graph /eval ┘
```

| Layer | Language | Owns |
| --- | --- | --- |
| **Crawler** | Go | Webhooks + filesystem watch, change detection, worker-pool fan-out |
| **Chunker** | Rust | Semantic (lexical-cohesion) chunking, markdown cleaning |
| **Engine** | Python | Hashing embeddings, vector store, RAG, Ragas-style eval |
| **Dashboard** | TypeScript | Knowledge graph + chat console + retrieval scores |

Runs **offline** — no sentence-transformers (a from-scratch hashing embedder),
no numpy, no LLM (extractive synthesis), no Ragas dependency (the metrics are
reimplemented). Real embedders/LLMs drop in via env vars.

## Quickstart — the engine, offline

```bash
cd engine-python && pip install -e ".[dev]"
python -m ragforge_engine.cli demo
```

```
Q: how do I request time off?
A: To request time off, open the HR portal and submit a leave request with your dates. ...

contexts:
  [0.7xx] hr/pto.md#1
  ...
scores: {'faithfulness': 0.9xx, 'answer_relevance': 0.xx, 'context_precision': ..., 'context_recall': ...}
```

Offline end-to-end check (seed → index → query → eval, no services):

```bash
python scripts/verify.py     # RESULT: N passed, 0 failed
```

## Quickstart — the whole pipeline

```bash
docker compose up --build
# Dashboard: http://localhost:3000   (knowledge graph + chat)
# Crawler:   http://localhost:8080/healthz
# Chunker:   http://localhost:8093/healthz
# Engine:    http://localhost:8000/healthz
```

The crawler watches a seeded `corpus/`; edit a file and the pipeline re-chunks
and re-indexes it within seconds. Push a change directly:

```bash
curl -XPOST localhost:8080/webhook -H 'content-type: application/json' \
  -d '{"doc_id":"notes/x.md","action":"upsert","text":"Refunds are processed within five business days."}'
```

## The interesting engineering

- **Semantic chunking (Rust)** — a TextTiling-style signal: split at local
  minima of adjacent-sentence lexical cohesion (Otsuka-Ochiai term-set cosine),
  capped by `max_words`, so chunks break where the topic changes.
  `chunker-rust/src/chunk.rs`
- **Hashing embedder (Python)** — the feature-hashing trick with signed buckets
  and sublinear TF, L2-normalised, fully deterministic (`hashlib`, not salted
  `hash()`), no numpy. `engine-python/ragforge_engine/embeddings.py`
- **RAG eval from scratch (Python)** — faithfulness, answer-relevance,
  context-precision and context-recall reimplemented as lexical approximations
  of the Ragas metrics. `engine-python/ragforge_engine/evaluate.py`
- **Change-driven crawler (Go)** — content-hash filesystem watch + webhooks feed
  a bounded queue + worker pool; a saturated pool drops rather than stalls.
  `crawler-go/internal/`

## Testing

```bash
make test                     # rust + go + python
cd chunker-rust && cargo test
cd crawler-go   && go test ./...
cd engine-python && pytest -q
cd dashboard-ts && npm run build
```

## Layout

```
proto/            shared JSON change / chunk / query protocol
dashboard-ts/     Next.js knowledge graph + chat console
crawler-go/       Go watcher + webhook crawler (+ seeded corpus/)
chunker-rust/     Rust semantic (topic-shift) chunker (axum)
engine-python/    hashing embedder + vector store + RAG + eval + FastAPI
scripts/verify.py offline end-to-end check
docs/ARCHITECTURE.md
```

## License

MIT © 2026 Akhil Vase
