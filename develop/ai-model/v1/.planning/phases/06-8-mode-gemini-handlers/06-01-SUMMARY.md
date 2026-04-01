---
phase: 06-8-mode-gemini-handlers
plan: "01"
subsystem: ai-chat-pipeline
tags: [gemini, schemas, pydantic, structured-output, mode-routing]
dependency_graph:
  requires: [05-chat-pipeline-core/05-02]
  provides: [8-mode-gemini-schema-routing]
  affects: [app/services/chat_service.py, app/schemas/gemini_outputs.py, app/schemas/chat.py]
tech_stack:
  added: []
  patterns: [Pydantic structured output schemas, mode-map dispatch, items-wrapper for Gemini list limitation]
key_files:
  created:
    - app/schemas/gemini_outputs.py
    - tests/test_gemini_outputs.py
  modified:
    - app/services/chat_service.py
    - tests/test_chat_service.py
    - app/schemas/chat.py
decisions:
  - Gemini top-level list 미지원으로 ExercisePlanOutput/MealPlanOutput에 items wrapper 패턴 사용
  - _MODE_SCHEMA_MAP dict로 모드별 스키마 O(1) 조회, 알 수 없는 모드는 SimpleAnswerOutput fallback
  - AiChatData.detail: Optional[Any]로 모드별 구조화 데이터 전달, 기존 plan/db_update 필드 유지
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_modified: 5
---

# Phase 06 Plan 01: 8-mode Gemini Output Schemas and Chat Service Mode Routing Summary

**One-liner:** Mode-specific Pydantic schemas for Gemini structured output (8 modes) with _MODE_SCHEMA_MAP dispatch and _build_ai_chat_data() per-mode response parser replacing Phase 5 single-schema placeholder.

## What Was Built

### Task 1: 8모드 Gemini 응답 스키마 정의 + AiChatData.detail 필드 추가

**Commit:** 9f51774

Created `app/schemas/gemini_outputs.py` with 9 Pydantic models organized by mode:
- `SimpleAnswerOutput(answer: str)` — mode 1
- `ExercisePlanItem` + `ExercisePlanOutput(items: list[ExercisePlanItem])` — modes 2, 3
- `MealPlanItem` + `MealPlanOutput(items: list[MealPlanItem])` — modes 4, 5
- `UserDbUpdateOutput(updated_fields: dict[str, Any])` — mode 6
- `MealLogOutput(calories, carbs, protein, fat, message)` — mode 7
- `RecommendationExercise` + `RecommendationMeal` + `RecommendationOutput` — mode 8

Added `detail: Optional[Any] = None` to `AiChatData` for mode-specific structured data payload.

Created `tests/test_gemini_outputs.py` with 16 tests (instantiation + JSON roundtrip for each schema).

### Task 2: _get_worker_response_schema() 모드별 분기 + 응답 파싱 로직 업데이트

**Commit:** c922907

Updated `app/services/chat_service.py`:
- Replaced Phase 5 local `SimpleAnswerOutput` class with import from `gemini_outputs`
- Added `_MODE_SCHEMA_MAP` dict for O(1) mode-to-schema dispatch
- Updated `_get_worker_response_schema()` to use the map with fallback
- Added `_build_ai_chat_data(mode, parsed)` helper covering all 8 modes
- Updated `handle_ai_chat()` to use `_build_ai_chat_data()` instead of single `parsed.get("answer")` line

Updated `tests/test_chat_service.py`:
- Fixed mode 2/6 mock JSON to use correct schema format (EXERCISE_PLAN_JSON, USER_DB_UPDATE_JSON)
- Added 2 sync tests for `_get_worker_response_schema()` (8 modes + unknown fallback)
- Added 5 sync tests for `_build_ai_chat_data()` (modes 1, 2, 6, 7, 8)

## Test Results

All 30 tests pass:
- `tests/test_gemini_outputs.py`: 16 passed
- `tests/test_chat_service.py`: 14 passed (7 original + 7 new)

## Decisions Made

1. **items wrapper pattern** — Gemini structured output does not support top-level list schemas. ExercisePlanOutput and MealPlanOutput use `items: list[...]` wrapper to satisfy Gemini's BaseModel requirement.

2. **_MODE_SCHEMA_MAP dict dispatch** — O(1) lookup vs if-elif chain, unknown modes gracefully fallback to SimpleAnswerOutput.

3. **detail: Optional[Any]** — Added to AiChatData alongside existing `plan` and `db_update` fields (kept for backward compatibility). The `detail` field carries mode-specific structured data for the WAS/frontend.

## Deviations from Plan

None - plan executed exactly as written.
