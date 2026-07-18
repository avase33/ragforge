# ragforge architecture

An automated vector data pipeline that keeps a RAG knowledge base fresh. Each
language owns its domain; one JSON contract (`proto/protocol.md`) connects them.

```
   Slack / Notion / GitHub / files
        │  webhook  ·  filesystem watch
        ▼
┌──────────────────────────┐  POST /chunk    ┌──────────────────────────┐
│ Crawler · Go             │ ──────────────▶ │ Chunker · Rust           │
│ change detection ·       │ ◀── chunks       │ topic-shift segmentation  │
│ queue + worker pool      │                 │ + markdown cleaning       │
└───────┬──────────────────┘                 └──────────────────────────┘
        │ POST /ingest  { chunks }
        ▼
┌──────────────────────────┐
│ Engine · Python          │  embed → vector store → retrieve → synthesise → eval
└───────┬──────────────────┘
        │ /query  /graph  /eval
        ▼
┌──────────────────────────┐
│ Dashboard · TypeScript   │  knowledge graph, chat console, retrieval scores
└──────────────────────────┘
```

## Why each language

| Layer | Language | Reason |
| --- | --- | --- |
| Crawler | **Go** | Many concurrent watchers/webhooks + a cheap worker pool. |
| Chunker | **Rust** | Fast text scanning and set math over large documents. |
| Engine | **Python** | Where embeddings, RAG, and eval live — here, from scratch. |
| Dashboard | **TypeScript** | Interactive graph + chat over the engine's API. |

## Flow

1. The Go crawler detects a change — a webhook `POST /webhook` or a content-hash
   difference found while walking the watch directory — and enqueues an
   `upsert` or `delete` event.
2. A worker sends the document to the Rust chunker, which cleans the markup and
   segments it at **topic shifts**: it measures lexical cohesion between adjacent
   sentences and cuts at local minima that dip below the document's mean
   cohesion (a TextTiling-style signal), capped by `max_words`.
3. The worker upserts the chunks into the Python engine, which embeds each chunk
   with a from-scratch hashing embedder and stores it in the vector store, keyed
   `doc_id#index`. A `delete` removes every chunk for the doc.
4. A query embeds the question, retrieves the top-k chunks by cosine, and
   synthesises an answer extractively (or via a real LLM if configured). The
   engine then **grades its own answer** with reimplemented Ragas metrics.
5. The dashboard renders the document/chunk graph and a chat console showing the
   answer, the retrieved contexts, and the four quality scores.

## Semantic chunking

For sentences `s0..sn`, cohesion `c[i]` between `s[i]` and `s[i+1]` is the
Otsuka-Ochiai coefficient over their content-term sets:

    c[i] = |terms(s_i) ∩ terms(s_{i+1})| / sqrt(|terms(s_i)| · |terms(s_{i+1})|)

A boundary is placed after `s[i]` when `c[i]` is a local minimum and below the
mean cohesion, or when the running chunk would exceed `max_words`. Chunks
therefore preserve topical coherence. See `chunker-rust/src/chunk.rs`.

## Eval

The engine reimplements the core Ragas signals as lexical approximations:
**context precision** (fraction of retrieved chunks sharing a term with the
answer), **context recall** (fraction of answer terms present in the contexts),
**faithfulness** (fraction of answer sentences mostly covered by the contexts),
and **answer relevance** (fraction of question terms reflected in the answer).
See `engine-python/ragforge_engine/evaluate.py`.

## Offline-first

- **Chunker**: pure text + set math, no NLP model.
- **Engine**: from-scratch hashing embeddings (no sentence-transformers, no
  numpy), extractive synthesis (no LLM), reimplemented eval (no Ragas). Seeds
  built-in corporate docs so the API is useful with no crawler.
- **Crawler**: a seeded `corpus/` and a synthetic-friendly watch loop.
- Real backends drop in via `RAGFORGE_LLM=openai` (and an embedder swap point).

`docker compose up` runs the full change→chunk→index→query loop; `make demo`
answers questions with no services at all.
