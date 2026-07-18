# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-07-17

Initial release — a four-language autonomous vector data engine for continuous RAG.

### Added
- **Rust chunker**: semantic (topic-shift) chunking via adjacent-sentence
  lexical cohesion (Otsuka-Ochiai term-set cosine, TextTiling-style boundaries),
  markdown cleaning, and a `max_words` cap. axum `/chunk`. Unit tests incl. a
  topic-shift split.
- **Go crawler**: content-hash filesystem watcher + webhook ingestion detecting
  add/modify/delete, a bounded queue + worker pool driving the chunker and
  engine, and a seeded corpus. Tests for change detection.
- **Python engine**: a from-scratch hashing embedder (feature hashing, signed
  buckets, sublinear TF, L2 norm), an in-memory vector store with delete-by-doc,
  extractive RAG synthesis, and reimplemented Ragas-style eval metrics
  (faithfulness, answer-relevance, context-precision/recall). FastAPI
  `/ingest` `/query` `/eval` `/graph`, CLI, seed corpus, tests + verifier.
- **Next.js dashboard**: a canvas knowledge graph of docs and chunks plus a chat
  console that shows the answer, retrieved contexts, and the four quality scores.
- Shared JSON protocol, docker-compose, per-service Dockerfiles, multi-language
  CI, Makefile, offline verifier, MIT license.
