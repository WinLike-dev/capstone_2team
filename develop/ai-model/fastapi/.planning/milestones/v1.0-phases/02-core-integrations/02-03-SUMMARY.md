---
phase: 02-core-integrations
plan: 03
subsystem: api
tags: [gemini, google-genai, tenacity, retry, prompts, mode7, mode8]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: UserProfile, MealAnalysisData, RecommendationData Pydantic schemas
provides:
  - GeminiClient with async generate() and tenacity 429 retry
  - build_meal_system_prompt() for Mode 7 (식단 분석)
  - build_recommend_system_prompt() for Mode 8 (추천)
affects:
  - 02-core-integrations (routers/meal.py, routers/recommend.py that call GeminiClient)
  - 03-ai-pipeline

# Tech tracking
tech-stack:
  added: [google-genai>=1.67.0, tenacity>=9.1.4]
  patterns: [GeminiClient wrapper pattern, prompt builder functions, tenacity retry_if_exception predicate]

key-files:
  created:
    - app/clients/gemini.py
    - app/prompts/meal.py
    - app/prompts/recommend.py
    - tests/test_gemini.py
  modified: []

key-decisions:
  - "google.api_core not available; use genai_errors.ClientError with code==429 check instead of ResourceExhausted"
  - "retry_if_exception(_is_resource_exhausted) predicate used over retry_if_exception_type to target 429 specifically"
  - "response_mime_type=application/json + response_schema enforces SDK-level JSON output"

patterns-established:
  - "Prompt builder pattern: CONSTANT for default prompt + build_*_prompt(user_profile) for personalized variant"
  - "GeminiClient._client replaced in tests via __new__ + direct attribute assignment for tenacity-compatible mocking"

requirements-completed: [GEMI-01, GEMI-02, GEMI-03, GEMI-04, GEMI-05]

# Metrics
duration: 10min
completed: 2026-03-22
---

# Phase 2 Plan 03: GeminiClient and Mode 7/8 Prompts Summary

**Async GeminiClient with tenacity exponential-backoff retry on HTTP 429, plus UserProfile-injecting prompt builders for Mode 7 (식단 분석) and Mode 8 (운동/식단 추천)**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-22T08:33:23Z
- **Completed:** 2026-03-22T08:43:00Z
- **Tasks:** 2
- **Files modified:** 4 (created)

## Accomplishments
- GeminiClient wraps google-genai SDK with async `generate()` enforcing JSON output via `response_mime_type` + `response_schema`
- tenacity retries only on `ClientError.code == 429` (exponential backoff initial=1s, max=60s, jitter=5, up to 5 attempts)
- `build_meal_system_prompt()` and `build_recommend_system_prompt()` inject all relevant UserProfile fields; None values become "정보 없음"
- 7 unit tests pass: API call params, response.text return, 429 retry, both prompt builders with full and empty profiles

## Task Commits

1. **Task 1: Mode 7/8 프롬프트 + GeminiClient 구현** - `ecf98f9` (feat)
2. **Task 2: GeminiClient 단위 테스트** - `2e4c85c` (test)

## Files Created/Modified
- `app/clients/gemini.py` - GeminiClient with async generate() and tenacity retry decorator
- `app/prompts/meal.py` - MEAL_ANALYSIS_SYSTEM_PROMPT constant + build_meal_system_prompt()
- `app/prompts/recommend.py` - RECOMMENDATION_SYSTEM_PROMPT constant + build_recommend_system_prompt()
- `tests/test_gemini.py` - 7 unit tests covering all specified behaviors

## Decisions Made
- `google.api_core` is not available in the current environment (google-genai 1.67.0 does not pull it as a dependency). Used `genai_errors.ClientError` with `exc.code == 429` predicate instead of the originally planned `ResourceExhausted` class.
- Used `retry_if_exception(_is_resource_exhausted)` helper function to keep the retry condition explicit and testable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced unavailable google.api_core.exceptions.ResourceExhausted with ClientError 429 predicate**
- **Found during:** Task 1 (import verification)
- **Issue:** `google.api_core` is not installed in the project environment; `from google.api_core.exceptions import ResourceExhausted` raised `ModuleNotFoundError`
- **Fix:** Used `google.genai.errors.ClientError` with `code == 429` check via a `_is_resource_exhausted()` predicate function passed to `retry_if_exception()`
- **Files modified:** app/clients/gemini.py
- **Verification:** `python -c "from app.clients.gemini import GeminiClient; ..."` outputs `Import OK`; all retry tests pass
- **Committed in:** ecf98f9 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (blocking import error)
**Impact on plan:** Required fix to meet the retry requirement. Behavior is equivalent — only 429 errors trigger retry, all other errors propagate immediately.

## Issues Encountered
None beyond the deviation above.

## User Setup Required
None - no external service configuration required at this stage. GEMINI_API_KEY is consumed by GeminiClient but not validated here (handled in config/lifespan).

## Next Phase Readiness
- GeminiClient ready to be injected into `/process-meal` and `/recommend` route handlers
- Prompt builders can be called directly with the `user_profile` field from request bodies
- No blockers

---
*Phase: 02-core-integrations*
*Completed: 2026-03-22*
