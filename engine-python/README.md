# ragforge-engine

The intelligence layer: a from-scratch **hashing embedder**, an in-memory
**vector store**, extractive **RAG**, and **Ragas-style eval** metrics — all
without numpy, sentence-transformers, or an LLM. Real backends drop in via
`RAGFORGE_LLM=openai`.

```bash
pip install -e ".[dev]"
python -m ragforge_engine.cli demo     # seed docs + answer a question + scores
python -m ragforge_engine.cli eval      # run the eval suite
ragforge-engine serve                   # FastAPI on :8000
pytest -q
```

Endpoints: `/ingest`, `/query`, `/eval`, `/graph`.
