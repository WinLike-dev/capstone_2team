---
phase: 03-endpoints-and-memory
plan: "01"
subsystem: background-summary-pipeline
tags: [background-summary, prompt-builder, context-injection, pinecone, gemini, tdd]
dependency_graph:
  requires: [02-core-integrations]
  provides: [run_background_summary, build_summary_prompt, SummaryOutput, context_text-prompt-builders]
  affects: [03-02-process-meal, 03-03-recommend]
tech_stack:
  added: []
  patterns: [try/except-silent-background-task, async-pipeline, default-param-backward-compat]
key_files:
  created:
    - app/prompts/summary.py
    - app/services/background_summary.py
    - tests/test_background_summary.py
    - tests/test_prompts.py
  modified:
    - app/prompts/meal.py
    - app/prompts/recommend.py
decisions:
  - "run_background_summary takes client instances directly (no Request injection) for clean DI and testability"
  - "SummaryOutput.summary is non-Optional to prevent silent empty summaries from Gemini"
  - "context_text default='이전 맥락: 없음' preserves backward compatibility with Phase 2 callers"
  - "Entire pipeline wrapped in try/except Exception with logger.exception() — never re-raises (BGSM-05)"
metrics:
  duration_seconds: 213
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 4
  files_modified: 2
---

# Phase 3 Plan 01: Background Summary Pipeline + Prompt Extension Summary

**One-liner:** Gemini 요약 -> 임베딩 -> Pinecone 저장 비동기 파이프라인과 프롬프트 빌더 context_text 주입 구현

## What Was Built

### Task 1: Summary Prompt + Background Summary Pipeline (TDD)

**app/prompts/summary.py**
- `SummaryOutput(BaseModel)`: `summary: str` (non-Optional) — Gemini JSON 응답 스키마
- `SUMMARY_SYSTEM_PROMPT`: 2-3문장 한국어 요약 지시
- `build_summary_prompt() -> str`: 시스템 프롬프트 반환

**app/services/background_summary.py**
- `run_background_summary(user_id, user_message, ai_response, gemini_client, embed_client, pinecone_client) -> None`
- 파이프라인: `build_summary_prompt()` → `gemini.generate(system_prompt, content, SummaryOutput)` → `json.loads` → `embed(summary_text)` → `pinecone.upsert(user_id, vector, summary_text)`
- 전체 `try/except Exception` 래핑: 에러 시 `logger.exception()` 호출 후 조용히 종료 (BGSM-05)

**tests/test_background_summary.py** — 5개 TDD 테스트:
- `test_summary_gemini_call`: generate() 인자 검증
- `test_summary_embed_call`: embed() Gemini 결과 전달 검증
- `test_summary_pinecone_upsert`: upsert() 인자 검증
- `test_summary_error_silent`: 예외 전파 없음 검증
- `test_summary_error_logging`: ERROR 레벨 로그 기록 검증

### Task 2: Prompt Builder context_text Extension

**app/prompts/meal.py**
- `build_meal_system_prompt(user_profile, context_text="이전 맥락: 없음") -> str`
- `f"{context_text}\n"` 를 "한국어로 응답하세요." 바로 앞에 삽입

**app/prompts/recommend.py**
- `build_recommend_system_prompt(user_profile, context_text="이전 맥락: 없음") -> str`
- 동일 패턴

**tests/test_prompts.py** — 4개 테스트:
- `test_meal_prompt_with_context`, `test_meal_prompt_default_context`
- `test_recommend_prompt_with_context`, `test_recommend_prompt_default_context`

## Test Results

```
tests/test_background_summary.py: 5 passed
tests/test_prompts.py: 4 passed
Total: 9 passed, 0 failed
```

Existing Phase 2 tests (test_gemini.py, test_embedding.py, etc.): all 41 unrelated tests pass.

Pre-existing failures (out of scope, not caused by this plan):
- `test_health.py::test_health_returns_200` — Missing `ROUTER_API_KEY` env var in test environment (pre-existing)
- `test_lifespan.py`, `test_stub_endpoints.py` — Same env var issue (pre-existing)

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **Client DI over Request injection**: `run_background_summary` receives client instances directly. Avoids Pitfall 1 (Request object not available in detached background tasks).
2. **non-Optional SummaryOutput.summary**: Forces Gemini to return a non-empty summary field. Silent empty summaries would produce useless embeddings.
3. **context_text default preserves backward compat**: Phase 2 `test_gemini.py` calls `build_meal_system_prompt(profile)` without context_text — still passes.
4. **Silent error handling**: Background summary failure must never crash the main response path. `logger.exception()` preserves full traceback in logs.

## Self-Check

- [x] app/prompts/summary.py exists
- [x] app/services/background_summary.py exists
- [x] tests/test_background_summary.py exists (5 tests pass)
- [x] tests/test_prompts.py exists (4 tests pass)
- [x] app/prompts/meal.py modified with context_text
- [x] app/prompts/recommend.py modified with context_text
- [x] Task 1 commit: 54ab17e
- [x] Task 2 commit: ff30bf8
