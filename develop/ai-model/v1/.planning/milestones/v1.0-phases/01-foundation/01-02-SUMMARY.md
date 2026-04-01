---
phase: 01-foundation
plan: 02
subsystem: api
tags: [pydantic, fastapi, schemas, stubs, endpoints]

# Dependency graph
requires:
  - phase: 01-foundation
    plan: 01
    provides: FastAPI app scaffold, core/config.py, core/lifespan.py, /health endpoint

provides:
  - Pydantic schemas matching docs/DataFormat_2_ai.md JSON spec (UserProfile, SuccessResponse, ErrorResponse, ProcessMealRequest, MealAnalysisData, RecommendRequest, RecommendationData, RecommendedExercise, RecommendedMeal)
  - POST /process-meal stub endpoint (200 on valid, 422 on invalid)
  - POST /recommend stub endpoint (200 on valid, 422 on invalid)
  - 16 tests covering schema validation and endpoint integration

affects:
  - 01-03 (any further foundation plans)
  - Phase 2 (Pinecone/vector memory - will reuse schemas)
  - Phase 3 (real Gemini logic replaces stubs in meal.py, recommend.py)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SuccessResponse envelope: {status: 'success', data: Any}"
    - "ErrorResponse envelope: {status: 'error', error: {code, message}}"
    - "Unified UserProfile model shared across all endpoints (all fields Optional)"
    - "Stub router pattern: APIRouter + placeholder return value, comment marks Phase 3 replacement point"

key-files:
  created:
    - app/schemas/common.py
    - app/schemas/meal.py
    - app/schemas/recommend.py
    - app/schemas/__init__.py
    - app/routers/meal.py
    - app/routers/recommend.py
    - tests/test_schemas.py
    - tests/test_stub_endpoints.py
  modified:
    - app/main.py

key-decisions:
  - "UserProfile unified model with all-optional fields shared across /process-meal and /recommend"
  - "Stubs return hardcoded data; Phase 3 replaces stub body only, not interface"
  - "Routers registered without prefix (routes are /process-meal and /recommend, not /api/v1/...)"

patterns-established:
  - "Schema modules: common.py for shared types, endpoint-specific files for request/response"
  - "Router files export a single `router = APIRouter(...)` and are included in main.py"
  - "Integration tests use httpx AsyncClient + ASGITransport, marked @pytest.mark.anyio"

requirements-completed:
  - FOUND-02

# Metrics
duration: 5min
completed: 2026-03-21
---

# Phase 1 Plan 2: API Contract Schemas and Stub Endpoints Summary

**Pydantic schemas matching WAS JSON contract + two stub endpoints (/process-meal, /recommend) ready for immediate WAS integration testing**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-21T17:06:40Z
- **Completed:** 2026-03-21T17:11:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- 9 Pydantic models covering full API contract from docs/DataFormat_2_ai.md
- POST /process-meal and POST /recommend stubs returning spec-compliant responses
- 18 total tests passing (2 health + 11 schema unit + 5 endpoint integration)
- WAS team can begin integration testing immediately against running server

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic 스키마 정의** - `5813d65` (feat)
2. **Task 2: 스텁 엔드포인트 + 라우터 등록** - `b29564a` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `app/schemas/common.py` - UserProfile (unified, all-optional), SuccessResponse, ErrorResponse, ErrorDetail
- `app/schemas/meal.py` - ProcessMealRequest, MealAnalysisData
- `app/schemas/recommend.py` - RecommendRequest, RecommendedExercise, RecommendedMeal, RecommendationData
- `app/schemas/__init__.py` - re-exports all schema models
- `app/routers/meal.py` - POST /process-meal stub endpoint
- `app/routers/recommend.py` - POST /recommend stub endpoint
- `app/main.py` - added include_router for meal and recommend routers
- `tests/test_schemas.py` - 11 schema unit tests
- `tests/test_stub_endpoints.py` - 5 integration tests

## Decisions Made

- UserProfile is a single unified model with all fields Optional — /process-meal uses medical_history/allergies, /recommend uses activity_level. Avoids duplication and simplifies Phase 3 integration.
- Routers registered without API prefix (routes are `/process-meal` and `/recommend` as-is, matching the DataFormat spec).
- Stubs return hardcoded data; Phase 3 replaces only the stub body, keeping the interface stable for WAS.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- API contract codified and stable — WAS team can test against running stubs immediately
- Schemas are the single source of truth; Phase 3 will only replace stub bodies in meal.py and recommend.py
- No blockers for Phase 2 (Pinecone/vector memory)

## Self-Check: PASSED

All 10 files verified present. Commits 5813d65 and b29564a confirmed in git log. 18/18 tests passing.

---
*Phase: 01-foundation*
*Completed: 2026-03-21*
