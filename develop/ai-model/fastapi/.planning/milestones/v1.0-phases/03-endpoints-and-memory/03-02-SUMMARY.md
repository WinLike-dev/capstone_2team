---
phase: 03-endpoints-and-memory
plan: "02"
subsystem: process-meal-pipeline
tags: [meal-service, endpoint, global-exception-handler, pinecone-context, gemini, tdd, background-tasks]
dependency_graph:
  requires: [03-01, 02-core-integrations]
  provides: [process_meal, global_exception_handler, POST /process-meal (real)]
  affects: [03-03-recommend]
tech_stack:
  added: []
  patterns: [graceful-degradation, try-except-clienterror, global-exception-handler, tdd-red-green]
key_files:
  created:
    - app/services/meal_service.py
    - tests/test_meal_service.py
    - tests/test_endpoints.py
  modified:
    - app/routers/meal.py
    - app/main.py
decisions:
  - "ASGITransport(raise_app_exceptions=False) required for testing global exception handler in httpx 0.28"
  - "_fetch_context() helper isolates Pinecone+embed logic with graceful degradation on any Exception"
  - "Gemini ClientError maps to HTTPException(500, GEMINI_ERROR); unexpected Exception maps to INTERNAL_ERROR via global handler"
metrics:
  duration_seconds: 235
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 3
  files_modified: 2
---

# Phase 3 Plan 02: process-meal Pipeline + Global Exception Handler Summary

**One-liner:** POST /process-meal stub 교체 — Pinecone 맥락 검색 -> Gemini 식단 분석 -> BackgroundTask 등록 전체 파이프라인 + 글로벌 500 핸들러 구현

## What Was Built

### Task 1: meal_service.py 구현 (TDD)

**app/services/meal_service.py**
- `process_meal(body, request, background_tasks) -> SuccessResponse`: 전체 파이프라인 오케스트레이터
- `_fetch_context(pinecone, embed, user_id, query) -> str`: Pinecone 맥락 검색 헬퍼
  - `embed.embed(user_message)` -> `pinecone.search(user_id, vector, top_k=3)` 순서 실행
  - 결과 포매팅: "이전 맥락:\n1. ...\n2. ..."
  - Exception 발생 시 `logger.warning()` 후 "이전 맥락: 없음" 반환 (graceful degradation)
- 파이프라인: `_fetch_context` → `build_meal_system_prompt(user_profile, context_text)` → `gemini.generate(prompt, user_message, MealAnalysisData)`
- Gemini 실패: `genai_errors.ClientError` → `HTTPException(500, GEMINI_ERROR)`
- BackgroundTask 등록: `background_tasks.add_task(run_background_summary, user_id=..., user_message=..., ai_response=data.message, ...)`
- 반환: `SuccessResponse(data=data.model_dump())`

**tests/test_meal_service.py** — 9개 TDD 유닛 테스트:
- `test_process_meal_passes_fields`: embed/search 인자 검증
- `test_process_meal_pinecone_search`: embed → search 호출 순서 검증
- `test_process_meal_pinecone_failure`: Pinecone 예외 → 정상 응답 (graceful degradation)
- `test_process_meal_context_injection`: 검색 결과 → "이전 맥락:\n1. ..." 형식 검증
- `test_process_meal_no_context`: 빈 결과 → "이전 맥락: 없음" 검증
- `test_process_meal_gemini_call`: generate() 인자 (user_message, MealAnalysisData) 검증
- `test_process_meal_response_format`: SuccessResponse(data={calories: float, message: str}) 검증
- `test_process_meal_gemini_failure`: ClientError → HTTPException(500, GEMINI_ERROR) 검증
- `test_background_task_registered`: add_task(run_background_summary, ...) 검증

### Task 2: 라우터 교체 + 글로벌 예외 핸들러 + 통합 테스트

**app/routers/meal.py**
- stub 제거, `process_meal_endpoint(body, request, background_tasks)` 로 교체
- `from app.services.meal_service import process_meal as handle_process_meal`
- `return await handle_process_meal(body, request, background_tasks)`

**app/main.py**
- `@app.exception_handler(Exception)` 글로벌 핸들러 등록
- `logger.error("Unhandled exception: ...", traceback.format_exc())`
- `JSONResponse(500, {"status": "error", "error": {"code": "INTERNAL_ERROR", "message": "내부 서버 오류..."}})` 반환

**tests/test_endpoints.py** — 3개 통합 테스트:
- `test_process_meal_calls_service`: 서비스 mock, 200 + success 응답 확인
- `test_process_meal_422_invalid_body`: 필수 필드 누락 → 422 (글로벌 핸들러 미간섭)
- `test_global_handler_500`: 서비스 Exception → 500 + INTERNAL_ERROR

## Test Results

```
tests/test_meal_service.py: 9 passed
tests/test_endpoints.py: 3 passed (+ 2 recommend tests from linter extension)
Total new: 12 passed, 0 failed
```

Full suite (excluding pre-existing env var failures):
```
64 passed, 0 failed
```

Pre-existing failures (out of scope — documented in 03-01-SUMMARY):
- `test_health.py::test_health_returns_200` — Missing ROUTER_API_KEY env var
- `test_lifespan.py` — Same env var issue
- `test_stub_endpoints.py` — Same env var issue

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ASGITransport parameter name**
- **Found during:** Task 2 (test_global_handler_500)
- **Issue:** `raise_server_exceptions` is not a valid parameter for httpx 0.28's ASGITransport; the correct parameter is `raise_app_exceptions`
- **Fix:** Used `ASGITransport(app=app, raise_app_exceptions=False)` to allow FastAPI's exception handler to respond instead of raising through to the test
- **Files modified:** tests/test_endpoints.py
- **Commit:** 7b7aa9c

## Decisions Made

1. **`_fetch_context` as private helper**: Isolates Pinecone + embed logic with its own try/except, making graceful degradation clean and testable.
2. **`raise_app_exceptions=False` for global handler tests**: httpx 0.28 requires this flag on ASGITransport to prevent ASGI exceptions from propagating to the test client; FastAPI's global handler then intercepts and returns JSONResponse.
3. **ClientError → GEMINI_ERROR, Exception → INTERNAL_ERROR**: Clear distinction between known Gemini API errors (client-facing GEMINI_ERROR code) and unknown exceptions (generic INTERNAL_ERROR via global handler).

## Self-Check

- [x] app/services/meal_service.py exists
- [x] app/routers/meal.py contains `from app.services.meal_service import process_meal`
- [x] app/main.py contains `exception_handler`
- [x] tests/test_meal_service.py exists (9 tests pass)
- [x] tests/test_endpoints.py exists (3+ tests pass)
- [x] Task 1 commit: 9440795
- [x] Task 2 commit: 7b7aa9c
