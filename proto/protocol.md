# ragforge wire protocol

Documents flow: source → Go crawler → Rust chunker → Python embed/index. Queries
flow: client → Python retrieve/synthesise/evaluate. One JSON contract.

## 1. Change event (source → Go crawler)

Webhook `POST /webhook` or emitted by the filesystem watcher:

```json
{ "doc_id": "wiki/onboarding.md", "action": "upsert", "text": "# Onboarding\n..." }
```

`action` ∈ `upsert | delete`. For a delete, `text` may be empty.

## 2. Chunk request/response (Go crawler → Rust `/chunk`)

Request:

```json
{ "doc_id": "wiki/onboarding.md", "text": "…", "max_words": 120 }
```

Response — semantically coherent chunks:

```json
{
  "doc_id": "wiki/onboarding.md",
  "chunks": [
    { "index": 0, "text": "…", "n_sentences": 4, "cohesion": 0.42 }
  ]
}
```

Boundaries are placed at **topic shifts** — local minima of lexical cohesion
between adjacent sentences (a TextTiling-style signal) — subject to a
`max_words` cap. `cohesion` is the mean adjacent-sentence similarity inside the
chunk.

## 3. Index request (Go crawler → Python `/ingest`)

```json
{ "doc_id": "wiki/onboarding.md", "action": "upsert", "chunks": [ { "index":0, "text":"…" } ] }
```

The Python layer embeds each chunk and upserts it into the vector store, keyed
by `doc_id#index`. `action: "delete"` removes all chunks for the doc.

## 4. Query (client → Python `/query`)

```json
{ "question": "how do I request time off?", "k": 4 }
```

→

```json
{
  "answer": "…",
  "contexts": [ { "id": "hr/pto.md#1", "text": "…", "score": 0.71 } ],
  "scores": { "faithfulness": 0.9, "answer_relevance": 0.7, "context_precision": 0.75, "context_recall": 0.8 }
}
```

## 5. Graph (client → Python `/graph`)

```json
{ "docs": [ { "doc_id":"hr/pto.md", "chunks": 3, "stale": false } ],
  "edges": [ { "from":"hr/pto.md", "to":"hr/pto.md#0" } ] }
```

## Ports

| service | port | protocol |
| --- | --- | --- |
| Go crawler | 8080 | HTTP `/webhook` `/scan` `/healthz` |
| Rust chunker | 8093 | HTTP `/chunk` `/healthz` |
| Python engine | 8000 | HTTP `/ingest` `/query` `/eval` `/graph` `/healthz` |
| TS dashboard | 3000 | HTTP |
