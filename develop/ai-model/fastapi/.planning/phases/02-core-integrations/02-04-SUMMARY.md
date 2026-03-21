---
phase: 02-core-integrations
plan: "04"
subsystem: api
tags: [gemini, router-ai, pydantic, anyio, pytest]

requires:
  - phase: 01-foundation
    provides: Settings pattern (pydantic-settings), app/clients/__init__.py stub

provides:
  - RouterClient with async classify() returning RouterOutput(mode, reason)
  - ROUTER_SYSTEM_PROMPT constant migrated from docs/router_system_instruction.txt
  - 5 unit tests with fully mocked genai.Client (no real API calls)

affects:
  - 02-core-integrations (lifespan init must instantiate RouterClient with ROUTER_API_KEY/ROUTER_MODEL_NAME)
  - 03-endpoints (v2 /ai-chat will consume RouterClient via app.state)

tech-stack:
  added: []
  patterns:
    - "RouterClient wraps google-genai SDK with separate API key and model from GeminiClient"
    - "JSON parse failure in classify() returns mode=1 fallback (RouterOutput, not exception)"
    - "Unit tests mock genai.Client at construction time via patch('app.clients.router.genai.Client')"

key-files:
  created:
    - app/prompts/__init__.py
    - app/prompts/router.py
    - app/clients/router.py
    - tests/test_router.py
  modified: []

key-decisions:
  - "RouterClient uses separate ROUTER_API_KEY and ROUTER_MODEL_NAME (not shared with GeminiClient)"
  - "Output schema is mode + reason only — no confidence score (per CONTEXT.md decision)"
  - "Fallback on ANY exception during classify() is mode=1 with fixed Korean reason string"

patterns-established:
  - "Prompt constants live in app/prompts/{name}.py as module-level str constants"
  - "AI client classes store genai.Client as self._client and model name as self._model_name"

requirements-completed: [ROUT-01, ROUT-02, ROUT-03]

duration: 5min
completed: "2026-03-22"
---

# Phase 2 Plan 04: Router AI Client Summary

**Gemini Flash Lite RouterClient with 6-mode intent classification, JSON fallback to mode=1, and 5 mocked unit tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-21T18:33:02Z
- **Completed:** 2026-03-21T18:38:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- RouterClient with async classify() method using google-genai SDK with separate ROUTER_API_KEY/ROUTER_MODEL_NAME
- ROUTER_SYSTEM_PROMPT constant migrated from docs/router_system_instruction.txt to app/prompts/router.py
- 5 unit tests verifying normal classification, system prompt delivery, and two fallback scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Router 시스템 프롬프트 + RouterClient 구현** - `67fa273` (feat)
2. **Task 2: RouterClient 단위 테스트** - `52abd39` (test)

## Files Created/Modified

- `app/prompts/__init__.py` - Package init for prompts module
- `app/prompts/router.py` - ROUTER_SYSTEM_PROMPT constant (1207 chars, migrated from docs/)
- `app/clients/router.py` - RouterOutput(BaseModel), RouterClient with classify()
- `tests/test_router.py` - 5 unit tests with fully mocked genai.Client

## Decisions Made

- RouterClient uses its own `ROUTER_API_KEY` and `ROUTER_MODEL_NAME` environment variables, not shared with GeminiClient — enforces independent operation and separate billing (per CONTEXT.md)
- Output schema is `mode: int` + `reason: str` only (no confidence score) — per CONTEXT.md decision to keep router output minimal
- Any exception in classify() (parse error, network error, etc.) triggers mode=1 fallback — safe degradation ensures the system always has a usable routing decision

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Two environment variables must be added before RouterClient can be used in production:
- `ROUTER_API_KEY` — separate Gemini API key for router
- `ROUTER_MODEL_NAME` — model name (default intended: `gemini-2.0-flash-lite`)

These are needed when lifespan initializes RouterClient in a future plan.

## Next Phase Readiness

- RouterClient is standalone and fully tested — ready for lifespan integration
- app.state.router_client initialization (lifespan.py) is the next integration step
- v2 /ai-chat endpoint will consume RouterClient via dependency injection on app.state

---
*Phase: 02-core-integrations*
*Completed: 2026-03-22*
