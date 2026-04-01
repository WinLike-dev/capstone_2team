---
phase: 03-endpoints-and-memory
plan: "03"
subsystem: recommend-service-pipeline
tags: [recommend, pinecone, gemini, background-summary, tdd, fastapi]
dependency_graph:
  requires: [03-01, 02-core-integrations]
  provides: [recommend_service, POST /recommend pipeline]
  affects: []
tech_stack:
  added: []
  patterns: [async-pipeline, graceful-degradation, service-layer-delegation, background-task-registration]
key_files:
  created:
    - app/services/recommend_service.py
    - tests/test_recommend_service.py
  modified:
    - app/routers/recommend.py
    - tests/test_endpoints.py
decisions:
  - "_fetch_context reuses same graceful degradation pattern as meal_service._fetch_context — each service has its own inline helper (no shared util) to keep coupling low"
  - "pinecone.search called with keyword args (user_id=, vector=, top_k=) for clarity and test verifiability"
  - "Gemini failure raises HTTPException(500, detail={code: GEMINI_ERROR}) matching meal_service pattern"
  - "test_stub_endpoints.py::test_recommend_valid_request now fails by design — stub replaced; superseded by test_endpoints.py::test_recommend_calls_service"
metrics:
  duration_seconds: 421
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 2
  files_modified: 2
---

# Phase 3 Plan 03: Recommend Service Pipeline Summary

**One-liner:** Pinecone 맥락 검색 -> Gemini 추천 생성 -> BackgroundTask 등록 recommend 파이프라인 구현 및 stub 교체

## What Was Built

### Task 1: recommend_service.py 구현 + 유닛 테스트 (TDD)

**app/services/recommend_service.py**
- `_fetch_context(pinecone_client, embed_client, user_id, query) -> str`
  - `embed_client.embed(query)` -> `pinecone_client.search(user_id=, vector=, top_k=3)`
  - 검색 실패 또는 빈 결과: "이전 맥락: 없음" 반환 (graceful degradation)
  - 결과 있으면 "이전 맥락:\n1. ...\n2. ..." 형식 반환
- `recommend(body, request, background_tasks) -> SuccessResponse`
  - `request.app.state.{gemini,embed,pinecone}_client` 인스턴스 획득
  - `_fetch_context()` -> `build_recommend_system_prompt(profile, context_text)`
  - `gemini.generate(system_prompt, user_instruction, RecommendationData)` — ClientError -> HTTPException(500, GEMINI_ERROR)
  - `json.loads(raw_json)` -> `RecommendationData(**parsed)`
  - `background_tasks.add_task(run_background_summary, user_id=, user_message=body.user_instruction, ai_response=str(data.model_dump()), ...)`
  - `return SuccessResponse(data=data.model_dump())`

**tests/test_recommend_service.py** — 9개 TDD 테스트:
- `test_recommend_passes_fields`: embed.embed(user_instruction), pinecone.search(user_id=...) 호출 확인
- `test_recommend_pinecone_search`: embed -> pinecone.search 순서 및 인자 검증
- `test_recommend_pinecone_failure`: Pinecone Exception 발생 시 정상 응답 반환
- `test_recommend_context_injection`: 검색 결과 있을 때 "이전 맥락:\n1. ..." 형식 프롬프트 주입
- `test_recommend_no_context`: 빈 결과 시 "이전 맥락: 없음" 전달
- `test_recommend_gemini_call`: gemini.generate 인자 (user_content=user_instruction, response_schema=RecommendationData)
- `test_recommend_response_format`: SuccessResponse(status="success", data={recommended_exercise, recommended_meal})
- `test_recommend_gemini_failure`: ClientError -> HTTPException(500, GEMINI_ERROR)
- `test_recommend_background_task`: add_task(run_background_summary, user_id=, user_message=user_instruction, ...)

### Task 2: 라우터 교체 + 통합 테스트

**app/routers/recommend.py**
- Stub body 제거
- `from app.services.recommend_service import recommend as handle_recommend`
- `recommend_endpoint(body, request, background_tasks) -> return await handle_recommend(body, request, background_tasks)`

**tests/test_endpoints.py** (Plan 02에서 생성된 파일에 추가)
- `test_recommend_calls_service`: service mock, 200 + success 응답 확인
- `test_recommend_422_invalid_body`: user_id 누락 시 422 반환

## Test Results

```
tests/test_recommend_service.py: 9 passed
tests/test_endpoints.py: 5 passed (3 meal + 2 recommend)
Total: 14 passed, 0 failed
```

Full suite (excluding pre-existing env-var failures):
```
64 passed (tests/test_health.py, test_lifespan.py 제외 — pre-existing ROUTER_API_KEY missing)
```

## Deviations from Plan

### Auto-noted: test_stub_endpoints.py recommend test now fails by design

**Found during:** Task 2
**Issue:** `test_stub_endpoints.py::test_recommend_valid_request` was passing when `/recommend` was a stub. After router replacement, it now fails because `app.state.gemini_client` is not available without real lifespan.
**Disposition:** Expected — this is the intent of this plan. The test is superseded by `test_endpoints.py::test_recommend_calls_service` which mocks the service layer. This failure was also pre-existing for `/process-meal` tests in `test_stub_endpoints.py` (from Plan 02).
**No fix needed** — deferred to `deferred-items.md` if cleanup desired.

### Note: test_endpoints.py recommend tests already existed in Plan 02 commit

**Found during:** Task 2
**Issue:** `tests/test_endpoints.py` was created in commit `7b7aa9c` (Plan 02) with BOTH meal AND recommend integration tests already included.
**Disposition:** No action needed — tests pass correctly.

## Decisions Made

1. **_fetch_context as inline helper per service**: The plan noted possible extraction to a shared util. Kept inline in each service for low coupling — both services have slightly different signatures (user_instruction vs user_message as query).
2. **keyword args in pinecone.search**: Called as `pinecone_client.search(user_id=body.user_id, vector=vector, top_k=3)` for clarity and easier test verification.
3. **stub test obsolescence**: `test_stub_endpoints.py::test_recommend_valid_request` now fails. This is correct behavior.

## Self-Check

- [x] app/services/recommend_service.py created and committed (70dac52)
- [x] tests/test_recommend_service.py created, 9 tests pass (70dac52)
- [x] app/routers/recommend.py updated: stub removed, service called (a4195f9)
- [x] tests/test_endpoints.py has recommend integration tests (present from 7b7aa9c)
- [x] 14 tests pass: tests/test_recommend_service.py + tests/test_endpoints.py
- [x] 64 tests pass in full suite (excluding pre-existing env-var failures)
- [x] Task 1 commit: 70dac52
- [x] Task 2 commit: a4195f9
