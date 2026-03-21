---
phase: 02-core-integrations
plan: 01
subsystem: embedding
tags: [embedding, sentence-transformers, settings, tdd]
dependency_graph:
  requires: []
  provides: [EmbeddingClient, EMBEDDING_DIM, Settings.GEMINI_MODEL_NAME, Settings.ROUTER_API_KEY, Settings.ROUTER_MODEL_NAME]
  affects: [app/clients/embedding.py, app/core/config.py, requirements.txt]
tech_stack:
  added: [sentence-transformers>=5.0, google-genai>=1.0, pinecone[asyncio]>=8.0, tenacity>=9.0]
  patterns: [run_in_threadpool for CPU offload, TDD with mocked SentenceTransformer]
key_files:
  created:
    - app/clients/embedding.py
    - tests/test_embedding.py
  modified:
    - app/core/config.py
    - requirements.txt
    - .env.example
decisions:
  - "EMBEDDING_DIM=384: paraphrase-multilingual-MiniLM-L12-v2 outputs 384-dim (CONTEXT.md 768 was incorrect)"
  - "run_in_threadpool used for encode() — keeps asyncio event loop unblocked during CPU-bound inference"
  - "EmbeddingClient takes model as constructor arg — enables dependency injection and easy mocking in tests"
metrics:
  duration: "~5 min"
  completed: "2026-03-21"
  tasks_completed: 2
  files_changed: 5
---

# Phase 2 Plan 01: Settings + EmbeddingClient Summary

Async EmbeddingClient wrapping SentenceTransformer via run_in_threadpool (384-dim, paraphrase-multilingual-MiniLM-L12-v2), plus Settings env vars for Phase 2 clients.

## What Was Built

### Task 1: Settings 환경변수 추가 + 의존성 업데이트

- Added 3 new fields to `Settings` class: `GEMINI_MODEL_NAME` (default: gemini-2.0-flash), `ROUTER_API_KEY` (required), `ROUTER_MODEL_NAME` (default: gemini-2.0-flash-lite)
- Added 4 Phase 2 dependencies to `requirements.txt`: `pinecone[asyncio]>=8.0`, `sentence-transformers>=5.0`, `google-genai>=1.0`, `tenacity>=9.0`
- Updated `.env.example` with new env var templates

**Commit:** `9b16588`

### Task 2: EmbeddingClient 구현 + 단위 테스트 (TDD)

- RED: Wrote 4 failing tests in `tests/test_embedding.py` (commit `f1582dd`)
- GREEN: Implemented `EmbeddingClient` in `app/clients/embedding.py` (commit `5ecf111`)
- All 4 tests pass

**Commits:** `f1582dd` (tests), `5ecf111` (implementation)

## Key Decisions Made

1. **EMBEDDING_DIM = 384** — paraphrase-multilingual-MiniLM-L12-v2 outputs 384-dim vectors. The CONTEXT.md value of 768 was incorrect per research. Pinecone index must be created with dimension=384.

2. **Constructor injection for model** — `EmbeddingClient.__init__(self, model)` accepts a `SentenceTransformer` instance rather than loading it internally. This enables easy mocking in tests and clean DI patterns.

3. **run_in_threadpool pattern** — `starlette.concurrency.run_in_threadpool` is used to offload the synchronous CPU-bound `encode()` call, keeping the asyncio event loop responsive during inference.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- app/clients/embedding.py: FOUND
- tests/test_embedding.py: FOUND
- app/core/config.py: FOUND
- 02-01-SUMMARY.md: FOUND
- Commit 9b16588: FOUND
- Commit f1582dd: FOUND
- Commit 5ecf111: FOUND

## Verification Results

```
python -c "from app.core.config import Settings; s = Settings.model_fields; assert 'GEMINI_MODEL_NAME' in s and 'ROUTER_API_KEY' in s and 'ROUTER_MODEL_NAME' in s; print('OK')"
# OK: all new fields present

python -m pytest tests/test_embedding.py -v
# 4 passed in 0.11s
```
