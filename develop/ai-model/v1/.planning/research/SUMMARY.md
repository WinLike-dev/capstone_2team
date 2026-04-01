# Project Research Summary

**Project:** FastAPI AI Orchestration Hub — Health/Exercise Recommendation Service
**Domain:** RAG + LLM multi-mode AI backend service (internal microservice)
**Researched:** 2026-03-21
**Confidence:** HIGH (stack verified against PyPI; architecture patterns verified against official docs)

## Executive Summary

This project is an internal AI orchestration microservice built with FastAPI, serving as the AI brain behind a health/exercise recommendation app. The Node.js WAS (Web Application Server) calls this hub for three operations: meal analysis (`/process-meal`), exercise/diet recommendations (`/recommend`), and open-ended AI chat (`/ai-chat`). The canonical approach for this class of service is a layered FastAPI architecture — thin routers that delegate to orchestration services, which in turn call thin client wrappers for each external system (Gemini Flash, Pinecone, Node.js WAS). All external calls must be async-native. The most distinctive element is the `/ai-chat` endpoint, which requires parallel intent routing and vector retrieval via `asyncio.gather`, followed by conditional WAS data fetching, and finally mode-specific Gemini generation — 8 distinct structured output schemas driven by a Router AI intent classifier.

The recommended technical approach centers on three core integrations: Google Gemini Flash (`google-genai==1.68.0`, the new SDK that replaces the deprecated `google-generativeai`) for generation, Pinecone (`pinecone[asyncio]==8.1.0` with `PineconeAsyncio`) for vector memory, and `sentence-transformers==5.3.0` for self-contained embedding generation. A critical architectural choice is using FastAPI's `BackgroundTasks` for the post-response memory pipeline (summarize → embed → Pinecone upsert), which keeps user-facing latency low while accumulating personalization context over time. Pinecone namespacing per `user_id` is mandatory from day one — retrofitting this later requires full index rebuild.

The primary risks are: (1) silent failure of background summary tasks degrading vector memory quality without any visible signal, (2) CPU-bound embedding generation blocking the async event loop under concurrent load, and (3) Router AI misclassification propagating through the entire pipeline. All three can be addressed with concrete patterns — structured logging with `try/except` in background tasks, `run_in_threadpool` for embedding calls, and confidence-scored Router AI output with fallback handling. The medical advice anti-feature boundary is also a real risk given ECRI's 2026 classification of AI health chatbot misuse as the top health tech hazard; the Router AI must include a hard-coded deflection path for clinical/diagnostic intent classes.

## Key Findings

### Recommended Stack

The stack is well-established and all versions are confirmed against PyPI as of 2026-03-21. FastAPI `0.135.1` with Pydantic v2 (`2.12.5`) is the clear foundation — the Rust-core Pydantic v2 delivers 2x+ serialization throughput and provides the JSON schema generation needed for Gemini structured output. The critical package naming distinction: use `google-genai` (new SDK, supports async) not `google-generativeai` (legacy, support ended November 2025). Use `pinecone[asyncio]` not `pinecone-client` (stale). Sentence-transformers requires Korean language consideration: `paraphrase-multilingual-MiniLM-L12-v2` (768-dim) for Korean support vs `all-MiniLM-L6-v2` (384-dim, English-only) — the Pinecone index dimension must match the model choice.

**Core technologies:**
- **FastAPI 0.135.1**: ASGI web framework — async-native, auto-generates OpenAPI, Pydantic v2 integrated
- **google-genai 1.68.0**: Gemini Flash client — new GA SDK with async support; replaces deprecated `google-generativeai`
- **pinecone[asyncio] 8.1.0**: Vector DB — `PineconeAsyncio` / `IndexAsyncio` for non-blocking event loop usage
- **sentence-transformers 5.3.0**: Self-contained embedding — no external embedding API dependency; use multilingual model for Korean
- **httpx 0.28.1**: Async HTTP client — for conditional WAS list fetches in `/ai-chat`; use shared `AsyncClient` via lifespan
- **pydantic-settings 2.13.1**: Config management — `BaseSettings` with `.env` file and `@lru_cache` for type-safe settings

### Expected Features

Research confirms the feature scope maps directly to 3 endpoints with a shared infrastructure layer. All P1 features are required for the WAS to have a working integration — none can be deferred without breaking the WAS contract.

**Must have (table stakes):**
- `POST /process-meal` — meal record analysis with structured calorie/nutrient output; validates the Gemini + structured output pattern
- `POST /recommend` — exercise/diet recommendation with RAG context from Pinecone; first endpoint using vector retrieval
- `POST /ai-chat` — intent-routed conversational AI with 8 structured output modes; the most complex endpoint
- Gemini Flash integration — foundational; all 3 endpoints depend on it
- Pinecone integration (read + write) — required for RAG in all endpoints and background memory pipeline
- Router AI intent classifier — gates the entire `/ai-chat` pipeline; misclassification = wrong output schema returned
- 8-mode structured Gemini output — WAS has built UI per mode; cannot be deferred if WAS UI is already complete
- Background Summary pipeline (async) — must ship from day one so memory accumulates; retrofitting requires historical data replay
- Self-contained embedding generation — required by Background Summary upsert and Pinecone query vector construction
- Conditional WAS list fetch in `/ai-chat` — part of defined spec; triggers only on numeric/list intent classifications
- Pydantic request/response schemas — defines the WAS ↔ FastAPI contract; must be agreed before parallel WAS integration work

**Should have (competitive):**
- Parallel async intent routing + vector retrieval (`asyncio.gather`) — reduces `/ai-chat` latency by ~50%
- Per-user Pinecone namespace isolation — data privacy and retrieval quality; mandatory from launch (not optional)
- Confidence-scored Router AI output with fallback — prevents misclassification from silently degrading UX
- Cold start fallback in recommendations — generic health baselines when vector memory is empty (first interaction)

**Defer (v2+):**
- Critic/validation module — explicitly deferred in PROJECT.md; mitigate in v1 via strong system prompts + RAG + structured output
- Streaming responses (SSE/WebSocket) — breaks current REST contract; adds infrastructure complexity without proportional benefit
- Photo/image meal recognition — requires separate CV pipeline; significant scope expansion
- Medical diagnosis / clinical advice — hard-blocked anti-feature; deflect via Router AI classification, not deferred

### Architecture Approach

The recommended architecture is a strict 4-layer separation: API routers (HTTP boundary only), Services (orchestration logic), Clients (one per external system), and Core utilities (embedding, logging, exceptions). This layering is the consistent recommendation across all architecture sources and enables testing services in isolation without HTTP overhead. The project directory structure is explicit: `app/api/`, `app/services/`, `app/clients/`, `app/schemas/`, `app/core/`. Dependency injection via FastAPI's `Depends()` system creates clients once at startup (lifespan event) and injects them — never instantiate clients at module scope or per-request. The Background Summary pipeline uses FastAPI `BackgroundTasks` for fire-and-forget memory writes — appropriate for capstone scale; upgrade path to Celery + Redis exists if task failure resilience becomes critical.

**Major components:**
1. **API Routers** (`app/api/`) — HTTP validation only; delegate immediately to services; inject `BackgroundTasks`
2. **ChatService** (`app/services/chat_service.py`) — parallel `asyncio.gather(router_ai.classify, pinecone.search)`, conditional WAS fetch, Gemini mode dispatch
3. **MealService / RecommendService** — sequential Pinecone retrieval then Gemini generation; simpler than ChatService
4. **BackgroundSummary** (`app/services/background_summary.py`) — post-response pipeline with explicit `try/except` + structured logging
5. **GeminiClient** (`app/clients/gemini_client.py`) — 8-mode structured calls with exponential backoff on 429; mode-specific prompt builders
6. **PineconeClient** (`app/clients/pinecone_client.py`) — `PineconeAsyncio`; all upsert/query calls enforce `namespace=user_id`
7. **RouterAI** (`app/clients/router_ai.py`) — intent classifier returning label + confidence score; fallback on low confidence
8. **EmbeddingService** (`app/core/embedding.py`) — wraps sentence-transformers via `run_in_threadpool` to avoid blocking event loop

### Critical Pitfalls

1. **Background Summary silent failure** — wrap entire pipeline in `try/except`, log with `logger.error()`, track success/failure counter in health endpoint; silent failure means vector memory stops accumulating with no visible signal

2. **CPU-bound embedding blocks async event loop** — always wrap `embedding_model.encode()` in `run_in_threadpool(embedding_model.encode, text)` or `asyncio.to_thread()`; direct calls in `async def` block all concurrent requests

3. **Pinecone namespace missing = user data cross-contamination** — enforce `namespace=str(user_id)` on every upsert AND query from day one; recovery cost is HIGH (full index rebuild); single-user local testing hides this bug

4. **Embedding model mismatch corrupts vector search** — centralize embedding model ID in a single `settings.EMBEDDING_MODEL_ID` constant; Pinecone index dimension must match model dimension; changing models requires full index rebuild

5. **Router AI misclassification cascades** — design Router AI output to include intent label + confidence score; implement fallback to default chat mode when confidence < 0.7; log classification decisions for accuracy monitoring

## Implications for Roadmap

Based on combined research across all 4 files, the dependency graph is clear and maps to a sequential build order. Each phase is blocked until the previous completes.

### Phase 1: Foundation and Schemas

**Rationale:** Config, logging, exception handling, and Pydantic schemas have zero external dependencies. Schemas define the WAS ↔ FastAPI contract — WAS integration work cannot start until schemas are published. Build these first to unblock everything downstream.
**Delivers:** Running FastAPI server with health check; `app/config.py` with all env vars; `app/core/` (logging, exceptions); all Pydantic request/response schemas for 3 endpoints; `.env.example` in repo
**Addresses:** Request validation at API boundary (table stakes); WAS REST communication interface (P1)
**Avoids:** No external integrations yet — eliminates integration risk from day one work

### Phase 2: Core Infrastructure (Embedding + Pinecone)

**Rationale:** Embedding service and Pinecone client are required by all 3 endpoints AND the Background Summary pipeline. They must be stable before any service layer can be built. Embedding model selection (Korean vs English) must be locked here — changing it later requires Pinecone index rebuild.
**Delivers:** `app/core/embedding.py` with `run_in_threadpool` wrapper; `app/clients/pinecone_client.py` with `PineconeAsyncio`; per-user `namespace=user_id` enforced on all operations; embedding dimension constant centralized in config
**Uses:** `sentence-transformers==5.3.0`, `pinecone[asyncio]==8.1.0`
**Avoids:** CPU-bound event loop blocking (Pitfall 2); Pinecone namespace missing (Pitfall 3); embedding model mismatch (Pitfall 5)

### Phase 3: Gemini Flash Integration

**Rationale:** Gemini client is the second foundational dependency (after Pinecone). All 3 endpoints require it. Building it in isolation — with retry logic and structured output — before wiring into services ensures reliability before complexity is added.
**Delivers:** `app/clients/gemini_client.py` with 8-mode structured output; exponential backoff on 429 errors; mode-specific prompt builders as separate testable functions; `app/clients/router_ai.py` with confidence score output
**Uses:** `google-genai==1.68.0` (NOT `google-generativeai`)
**Avoids:** Gemini 429 cascading failures; Router AI misclassification (Pitfall 4); monolithic GeminiClient anti-pattern

### Phase 4: Simple Endpoints (Meal + Recommend)

**Rationale:** `/process-meal` and `/recommend` share the same simpler pattern (Pinecone search → Gemini generation → Background Summary) with no parallel async or conditional WAS fetch. Build and validate this pattern end-to-end before tackling the complex `/ai-chat` endpoint.
**Delivers:** `MealService`, `RecommendService`; `POST /process-meal`, `POST /recommend` routes wired end-to-end; Background Summary pipeline for both endpoints
**Implements:** Thin Router + Thick Service pattern; BackgroundTasks injection in routers
**Avoids:** Background Summary silent failure (Pitfall 1) — explicit error handling required before moving to Phase 5

### Phase 5: AI Chat Endpoint

**Rationale:** `/ai-chat` is the most complex endpoint and depends on everything built in Phases 1-4 (Pinecone, Gemini, Router AI, embedding, Background Summary). Building it last means the parallel async pattern and conditional WAS fetch are layered onto a stable base.
**Delivers:** `ChatService` with `asyncio.gather(router_ai.classify, pinecone.search)`; conditional WAS list fetch via `WASClient`; 8-mode Gemini dispatch; `POST /ai-chat` route
**Uses:** `httpx.AsyncClient` (shared instance via lifespan); `app/clients/was_client.py` with timeout configuration
**Avoids:** Sequential I/O anti-pattern; WAS connection pool waste; graceful degradation on WAS list fetch failure

### Phase 6: Integration Testing and Hardening

**Rationale:** Research identifies 8 specific "looks done but isn't" scenarios that require explicit integration tests. These cannot be verified by unit tests alone. This phase ensures the system is actually correct, not just apparently correct.
**Delivers:** Integration tests for each endpoint against mocked external services; user isolation test (two users, no cross-contamination); Background Summary round-trip verification (Pinecone vector count increase); Router AI boundary case tests (8 intents + ambiguous inputs); WAS mock with timeout/500 scenarios
**Avoids:** All 5 critical pitfalls — each has a corresponding verifiable test case

### Phase Ordering Rationale

- Phases 1-2 have no external dependencies and produce artifacts (schemas, Pinecone client) that unblock WAS parallel development
- Embedding model selection must happen in Phase 2 because changing it in Phase 4+ requires full Pinecone index rebuild — a HIGH recovery cost
- Background Summary ships in Phase 4 (not deferred to later) because retrofitting requires historical data replay
- `/ai-chat` is deliberately last because it depends on all other components; building it first would require extensive mocking that would need to be replaced
- Pinecone namespace isolation is enforced in Phase 2 (not Phase 5) because recovery from missing namespace is a full index rebuild

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Gemini Client / Router AI):** Prompt engineering for 8-mode structured output and Router AI intent classification requires domain-specific experimentation; generic documentation does not cover health/exercise domain prompt patterns
- **Phase 5 (AI Chat):** Graceful degradation strategy when WAS list fetch times out or returns 500 — behavior needs explicit product decision before implementation

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** FastAPI project structure and Pydantic settings are well-documented with established community patterns
- **Phase 2 (Pinecone + Embedding):** Pinecone asyncio client and sentence-transformers are well-documented; patterns are explicit in STACK.md
- **Phase 6 (Testing):** pytest + pytest-asyncio patterns are standard; no research needed

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI on 2026-03-21; official SDK migration path confirmed (`google-genai` vs `google-generativeai`) |
| Features | MEDIUM | Table stakes and must-haves are clear from domain research; 8-mode Gemini output schema details depend on product decisions not yet fully specified |
| Architecture | HIGH | Layered FastAPI + RAG patterns verified against FastAPI official docs, Pinecone official docs, and multiple production-grade reference implementations |
| Pitfalls | HIGH | Critical pitfalls verified against official FastAPI docs, Pinecone multi-tenancy docs, OWASP Gen AI, JAMA Network — not just blog posts |

**Overall confidence:** HIGH

### Gaps to Address

- **Korean language embedding quality:** `paraphrase-multilingual-MiniLM-L12-v2` vs `all-MiniLM-L6-v2` — validate retrieval quality with real Korean health domain text before committing to an embedding model in Phase 2; the choice locks the Pinecone index dimension
- **8-mode output schema contract with WAS:** The exact JSON schema for each of the 8 chat modes must be agreed with the WAS team before Phase 3 implementation; misalignment here breaks WAS rendering code
- **Router AI confidence threshold calibration:** The 0.7 fallback threshold is a starting point; actual threshold requires empirical testing with domain-specific queries to determine the right balance between fallback rate and misclassification rate
- **Gemini Flash rate limits at capstone scale:** TPM/RPM/RPD limits on the free tier may be restrictive under concurrent testing; validate limits before load testing Phase 6

## Sources

### Primary (HIGH confidence)
- PyPI package pages (fastapi, google-genai, pinecone, sentence-transformers, httpx, pydantic, uvicorn) — version verification, 2026-03-21
- FastAPI Official Docs: BackgroundTasks, Dependency Injection, lifespan events
- Pinecone Official Docs: PineconeAsyncio, multi-tenancy / namespace isolation
- Gemini API Docs: Rate limits, `google-genai` SDK migration
- OWASP Gen AI Security Project: LLM01:2025 Prompt Injection
- JAMA Network Open: Vulnerability of LLMs to prompt injection in medical advice (2024)
- ECRI: Top health tech hazards 2026 — AI chatbot misuse
- DietGlance (arXiv 2502.01317): Dietary monitoring with AI assistant
- PLOS Digital Health: AI-driven personalized nutrition RAG solution

### Secondary (MEDIUM confidence)
- FastAPI Best Practices (zhanymkanov GitHub) — project structure patterns
- Agents Arcade: Building LLM apps with FastAPI — thin router patterns
- Leapcell: Understanding async task management pitfalls in FastAPI
- Building a RAG-Powered Nutrition Chatbot with FastAPI and Pinecone (wellally.tech)
- Async RAG System with FastAPI, Qdrant, LangChain (futuresmart.ai)
- FastAPI + Celery background tasks comparison (TestDriven.io)
- AI Agent Routing tutorial and best practices (Patronus AI)

### Tertiary (LOW confidence)
- AI fitness app landscape blogs (Fitbod, Vora, Tribe AI) — feature benchmarking only; not used for technical decisions

---
*Research completed: 2026-03-21*
*Ready for roadmap: yes*
