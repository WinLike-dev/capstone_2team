---
phase: 04-infrastructure
plan: 02
subsystem: infrastructure
tags: [was-client, httpx, schemas, pydantic, ai-chat]
dependency_graph:
  requires: [04-01]
  provides: [WASClient, AiChatRequest, AiChatResponse, get_db_modified_flag]
  affects: [05-chat-pipeline, 06-mode-handlers]
tech_stack:
  added: [httpx.AsyncClient, httpx.MockTransport]
  patterns: [async HTTP client, Pydantic schema, mode-to-flag mapping]
key_files:
  created:
    - app/clients/was.py
    - app/schemas/chat.py
    - tests/test_was_client.py
  modified:
    - app/clients/__init__.py
    - app/core/lifespan.py
    - tests/test_schemas.py
decisions:
  - "ExternalServiceError imported from app.core.exceptions (Plan 01 completed); was.py placeholder approach not needed"
  - "db_modified_flag determined by FastAPI get_db_modified_flag() — Gemini does not decide"
  - "WASClient initialized in lifespan with httpx.AsyncClient(timeout=10s), stored as app.state.was_client"
metrics:
  duration: "~15 minutes"
  completed: "2026-03-22"
  tasks_completed: 2
  files_changed: 6
---

# Phase 4 Plan 02: WAS Client and AI Chat Schemas Summary

**One-liner:** httpx-based WASClient for exercise/meal list fetch + Pydantic AiChat schemas with deterministic db_modified_flag mapping.

## What Was Built

### Task 1: WAS HTTP Client

`app/clients/was.py` — `WASClient` wrapping `httpx.AsyncClient`:
- `fetch_exercise_list(user_id)` — GET `/api/exercise-list/{user_id}` -> `list[dict]`
- `fetch_meal_list(user_id)` — GET `/api/meal-list/{user_id}` -> `list[dict]`
- HTTP 4xx/5xx -> `ExternalServiceError(service="WAS", message="HTTP {status}")`
- Timeout -> `ExternalServiceError(service="WAS", message="request timeout")`

`app/clients/__init__.py` — added `WASClient` re-export.

`app/core/lifespan.py` — added step 5 to startup:
```python
http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
app.state.was_client = WASClient(base_url=settings.WAS_BASE_URL, client=http_client)
```
Shutdown closes the httpx client via `await app.state._was_http_client.aclose()`.

### Task 2: AI Chat Schemas

`app/schemas/chat.py`:
- `AiChatRequest` — user_id, user_profile, user_instruction, user_message
- `AiChatResponse` — status, mode, data (AiChatData), db_modified_flag
- `AiChatData` — message, plan (Optional[PlanData]), db_update (Optional[DbUpdate])
- `DbModifiedFlag = Literal["none", "exercise", "meal", "profile"]`
- `get_db_modified_flag(mode)` — deterministic mapping per project decision

## Test Results

| Test File | Tests | Result |
|---|---|---|
| tests/test_was_client.py | 7 | PASSED |
| tests/test_schemas.py (new additions) | 15 | PASSED |
| tests/test_lifespan.py | 6 | PASSED |
| **Total new tests** | **22** | **ALL PASSED** |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ExternalServiceError interface mismatch**
- **Found during:** Task 1 implementation
- **Issue:** Plan specified a placeholder `ExternalServiceError` with `service` and `message` dataclass fields. The real `ExternalServiceError` in `app/core/exceptions.py` (Plan 01) inherits from `AppError` — it concatenates service into `self.message` and exposes `error_code` instead of `service`.
- **Fix:** Updated `was.py` to import from `app.core.exceptions` directly (no placeholder needed). Updated tests to assert `error_code == "EXTERNAL_SERVICE_ERROR"` and check `"WAS" in message` instead of `exc.service == "WAS"`.
- **Files modified:** `app/clients/was.py`, `tests/test_was_client.py`
- **Commit:** 369fcea

**2. [Rule 3 - Blocking] pytest-asyncio not configured**
- **Found during:** Task 1 test execution
- **Issue:** Tests used `@pytest.mark.asyncio` but the project uses `pytest-anyio` (seen in existing tests). The `asyncio` mark was not recognized.
- **Fix:** Changed to `pytestmark = pytest.mark.anyio` at module level, matching the project convention in `test_lifespan.py`.
- **Files modified:** `tests/test_was_client.py`
- **Commit:** 369fcea

## Self-Check
