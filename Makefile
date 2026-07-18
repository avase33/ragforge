.PHONY: up down test test-rust test-go test-python build-web demo eval verify

up:
	docker compose up --build

down:
	docker compose down

test: test-rust test-go test-python

test-rust:
	cd chunker-rust && cargo test

test-go:
	cd crawler-go && go test ./...

test-python:
	cd engine-python && pip install -e ".[dev]" && pytest -q

build-web:
	cd dashboard-ts && npm install && npm run build

# Offline: seed docs, answer a question, show retrieval + eval scores.
demo:
	cd engine-python && python -m ragforge_engine.cli demo

eval:
	cd engine-python && python -m ragforge_engine.cli eval

verify:
	python scripts/verify.py
