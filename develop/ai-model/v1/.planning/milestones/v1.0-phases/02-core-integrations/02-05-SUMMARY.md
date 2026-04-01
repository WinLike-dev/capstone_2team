---
phase: 02-core-integrations
plan: 05
subsystem: infra
tags: [fastapi, lifespan, sentence-transformers, pinecone, gemini, google-genai]

# Dependency graph
requires:
  - phase: 02-core-integrations plan 01
    provides: EmbeddingClient, EMBEDDING_DIM (384-dim, run_in_threadpool)
  - phase: 02-core-integrations plan 02
    provides: PineconeClient (async upsert/search, namespace isolation)
  - phase: 02-core-integrations plan 03
    provides: GeminiClient (tenacity retry, response_schema)
  - phase: 02-core-integrations plan 04
    provides: RouterClient (Flash Lite, 6 modes), RouterOutput

provides:
  - FastAPI lifespan that initializes all 4 clients on startup
  - app.state.embed_client, pinecone_client, gemini_client, router_client available to request handlers
  - Pinecone connection cleanup on shutdown
  - clients/__init__.py re-exports for EmbeddingClient, PineconeClient, GeminiClient, RouterClient, RouterOutput, EMBEDDING_DIM
  - conftest.py stub for sentence_transformers (unblocks test collection without installed package)

affects: [03-endpoints, request-handlers, integration-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lifespan context manager for client lifecycle management"
    - "Module-level SentenceTransformer import enables patch() targeting in tests"
    - "sys.modules stub in conftest.py for optional heavy dependencies"
    - "PineconeAsyncio control-plane stored as app.state._pinecone_control for shutdown"

key-files:
  created:
    - app/clients/__init__.py
    - tests/test_lifespan.py
    - conftest.py
  modified:
    - app/core/lifespan.py

key-decisions:
  - "SentenceTransformer imported at module level (not inside lifespan) so tests can patch it via app.core.lifespan.SentenceTransformer"
  - "conftest.py injects sentence_transformers stub into sys.modules to unblock test collection when package not installed"
  - "Exceptions not caught in lifespan startup — propagate to abort server on partial init"
  - "Pre-existing test_health_returns_200 failure (missing ROUTER_API_KEY in .env) logged as out-of-scope"

patterns-established:
  - "Pattern 1: Use conftest.py sys.modules stubs for optional heavy libraries not installed in CI"
  - "Pattern 2: Module-level imports of patchable dependencies for testability"

requirements-completed: [PINE-01, EMBD-01, GEMI-01, ROUT-01]

# Metrics
duration: 12min
completed: 2026-03-21
---

# Phase 2 Plan 05: Lifespan Client Initialization Summary

**FastAPI lifespan wires all 4 clients (EmbeddingClient, PineconeClient, GeminiClient, RouterClient) into app.state with ordered startup and Pinecone shutdown cleanup**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-21T18:42:04Z
- **Completed:** 2026-03-21T18:54:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Lifespan initializes clients in declared order: Embedding -> Pinecone -> Gemini -> Router
- All 4 clients accessible via app.state in every request handler
- Pinecone control-plane connection properly closed on shutdown
- 6 unit tests covering all state assignments, shutdown, and error propagation
- conftest.py unblocks all test collection without requiring sentence_transformers installed

## Task Commits

Each task was committed atomically:

1. **Task 1: Lifespan init/shutdown + clients __init__ re-exports** - `e20bf09` (feat)
2. **Task 2: Lifespan unit tests (TDD GREEN)** - `203c0f4` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `app/core/lifespan.py` - Full lifespan with ordered client initialization and Pinecone shutdown
- `app/clients/__init__.py` - Re-exports EmbeddingClient, EMBEDDING_DIM, PineconeClient, GeminiClient, RouterClient, RouterOutput
- `tests/test_lifespan.py` - 6 unit tests for lifespan startup/shutdown behavior
- `conftest.py` - Root conftest that stubs sentence_transformers into sys.modules for all tests

## Decisions Made

- SentenceTransformer moved to module-level import so `patch("app.core.lifespan.SentenceTransformer")` works in tests
- Root `conftest.py` uses `sys.modules.setdefault` to inject a stub for `sentence_transformers` (large ML package, not installed in this environment) before any test module is collected
- Lifespan does not catch exceptions during startup — failures propagate and FastAPI aborts server start (prevents partial-init serving requests)
- `app.state._pinecone_control` stores the `PineconeAsyncio` instance (not the index) for `close()` in shutdown

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Moved SentenceTransformer import to module level for patchability**
- **Found during:** Task 2 (writing tests)
- **Issue:** Original plan showed local import inside lifespan function body; `patch("app.core.lifespan.SentenceTransformer")` fails for local imports since the name doesn't exist at module scope
- **Fix:** Import `from sentence_transformers import SentenceTransformer` at top of `lifespan.py` module
- **Files modified:** app/core/lifespan.py
- **Verification:** Tests pass after fix
- **Committed in:** 203c0f4 (Task 2 commit)

**2. [Rule 3 - Blocking] Added conftest.py to stub sentence_transformers**
- **Found during:** Task 2 (running full test suite)
- **Issue:** `sentence_transformers` not installed in environment; module-level import blocked test collection for test_health.py and test_stub_endpoints.py via `app.main` -> `app.core.lifespan`
- **Fix:** Created root `conftest.py` that injects a `MagicMock`-based stub module into `sys.modules["sentence_transformers"]` before any test is collected
- **Files modified:** conftest.py (new)
- **Verification:** Full test suite collects and runs (44 pass, 1 pre-existing failure)
- **Committed in:** 203c0f4 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug/testability, 1 blocking)
**Impact on plan:** Both required for test infrastructure correctness. No scope creep.

## Issues Encountered

- `test_health_returns_200` was already failing before this plan due to missing `ROUTER_API_KEY` in `.env` file (added in plan 02-01 but not yet set in local env). This is a pre-existing out-of-scope issue logged to deferred-items.

## User Setup Required

None — no external service configuration required beyond what was already needed.

## Next Phase Readiness

- All 4 clients are initialized in lifespan and accessible via `app.state` in request handlers
- Phase 3 endpoints can use `request.app.state.embed_client`, `request.app.state.pinecone_client`, etc.
- Phase 02 Wave 2 complete — lifespan wiring done
- Remaining concern: `ROUTER_API_KEY` must be added to `.env` before running the server (pre-existing gap)

---
*Phase: 02-core-integrations*
*Completed: 2026-03-21*
