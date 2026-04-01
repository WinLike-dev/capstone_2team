# Architecture Research

**Domain:** FastAPI AI Orchestration Hub (Health/Exercise — RAG + LLM multi-mode)
**Researched:** 2026-03-21
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Layer                           │
│  ┌──────────────────────────┐                                   │
│  │  Node.js WAS (REST API)  │                                   │
│  └────────────┬─────────────┘                                   │
└───────────────┼─────────────────────────────────────────────────┘
                │ HTTP REST
┌───────────────┼─────────────────────────────────────────────────┐
│               ▼          FastAPI Hub                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                     API Layer (Routers)                 │     │
│  │  /process-meal   /recommend   /ai-chat                 │     │
│  └─────────────────────────┬──────────────────────────────┘     │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────────┐     │
│  │                  Orchestration Layer (Services)         │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │     │
│  │  │ MealService  │  │RecommendSvc  │  │ ChatService │  │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  │     │
│  └─────────┼─────────────────┼─────────────────┼──────────┘     │
│            │                 │                 │                 │
│  ┌─────────▼─────────────────▼─────────────────▼──────────┐     │
│  │                  Integration Layer (Clients)            │     │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │     │
│  │  │ RouterAI   │  │GeminiClient│  │PineconeClient    │  │     │
│  │  │(intent clf)│  │(LLM calls) │  │(vector search/   │  │     │
│  │  └────────────┘  └────────────┘  │ store)           │  │     │
│  │                                  └──────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │         Background Layer (Async Memory Pipeline)        │     │
│  │  Request complete → LLM summary → embed → Pinecone store│     │
│  └─────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                │                               │
┌───────────────▼───────────────┐   ┌───────────▼────────────────┐
│   External AI Services        │   │  External Storage           │
│  ┌──────────┐  ┌───────────┐  │   │  ┌──────────────────────┐  │
│  │  Gemini  │  │ Router AI │  │   │  │  Pinecone Vector DB  │  │
│  │  Flash   │  │  (LLM)    │  │   │  │  (cloud-managed)     │  │
│  └──────────┘  └───────────┘  │   │  └──────────────────────┘  │
└───────────────────────────────┘   └────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| API Routers | HTTP request/response, input validation, BackgroundTasks injection | FastAPI router modules per endpoint group |
| MealService | Orchestrate VDB search + Gemini analysis for /process-meal | Python service class, called by router |
| RecommendService | Orchestrate VDB search + Gemini recommendation for /recommend | Python service class, called by router |
| ChatService | Parallel Router AI + VDB search, conditional WAS call, Gemini 8-mode dispatch | Python service class with asyncio.gather |
| RouterAI Client | LLM-based intent classification — determines chat mode (1 of 8) | Thin client wrapping a Gemini prompt or lightweight classifier |
| GeminiClient | Wrapper around Google Gemini Flash API; mode-aware structured response | Single client, method-per-mode or mode param |
| PineconeClient | Vector search (query) and upsert (store); embedding generation | Wraps Pinecone SDK v3+ with async support |
| EmbeddingService | Convert text to vectors using local embedding model | Sentence-Transformers or Google embedding API |
| BackgroundSummary | Post-response pipeline: LLM summary → embed → Pinecone upsert | FastAPI BackgroundTasks or asyncio.create_task |
| WASClient | HTTP client for conditional data requests to Node.js WAS | httpx async client |
| Config | Env-based settings via Pydantic BaseSettings | Single config.py at root |

## Recommended Project Structure

```
fastapi/
├── app/
│   ├── main.py                  # FastAPI app init, router registration, lifespan
│   ├── config.py                # Pydantic BaseSettings (env vars, API keys)
│   ├── dependencies.py          # Shared DI: get_pinecone, get_gemini_client, etc.
│   │
│   ├── api/                     # Routers — HTTP boundary only
│   │   ├── __init__.py
│   │   ├── meal.py              # POST /process-meal
│   │   ├── recommend.py         # POST /recommend
│   │   └── chat.py              # POST /ai-chat
│   │
│   ├── services/                # Orchestration logic — no HTTP concern
│   │   ├── __init__.py
│   │   ├── meal_service.py      # VDB search + Gemini analysis pipeline
│   │   ├── recommend_service.py # VDB search + Gemini recommend pipeline
│   │   ├── chat_service.py      # Parallel intent + VDB, conditional WAS, Gemini dispatch
│   │   └── background_summary.py# Async: summarize → embed → upsert pipeline
│   │
│   ├── clients/                 # External service wrappers — one per external system
│   │   ├── __init__.py
│   │   ├── gemini_client.py     # Gemini Flash API; 8-mode structured calls
│   │   ├── pinecone_client.py   # Pinecone vector search + upsert
│   │   ├── router_ai.py         # Intent classifier (LLM-based routing)
│   │   └── was_client.py        # httpx async client for Node.js WAS
│   │
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── meal.py
│   │   ├── recommend.py
│   │   └── chat.py
│   │
│   └── core/                    # Cross-cutting concerns
│       ├── __init__.py
│       ├── embedding.py         # Text-to-vector (sentence-transformers or API)
│       ├── exceptions.py        # Custom exception classes
│       └── logging.py           # Structured logging setup
│
├── tests/
│   ├── test_api/                # Route-level tests
│   ├── test_services/           # Service orchestration tests (mock clients)
│   └── test_clients/            # Client wrapper tests (mock external APIs)
│
├── .env                         # Local secrets (never committed)
├── .env.example                 # Template with key names, no values
├── requirements.txt
└── Dockerfile
```

### Structure Rationale

- **api/**: Routers own only HTTP concerns — validation, status codes, BackgroundTasks. Zero business logic here. Thin by design.
- **services/**: All orchestration logic lives here. Services call clients, compose results, and decide what to do. Services are testable without HTTP.
- **clients/**: One file per external system. Each client is a thin adapter — it wraps SDK calls and maps exceptions to domain exceptions. Swappable.
- **schemas/**: Pydantic models are the contract between HTTP layer and services. Keeps validation centralized.
- **core/**: Cross-cutting utilities (embedding, logging, exceptions) that don't belong to any single service or client.

## Architectural Patterns

### Pattern 1: Thin Router, Thick Service

**What:** Routers validate input and delegate immediately to a service. All orchestration logic lives in the service.
**When to use:** Always — the standard pattern for FastAPI LLM systems. Enables testing services without HTTP overhead.
**Trade-offs:** Slightly more files, but each file is focused and testable.

**Example:**
```python
# api/chat.py — thin
@router.post("/ai-chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
):
    result = await chat_service.process(request)
    background_tasks.add_task(background_summary.run, request, result)
    return result

# services/chat_service.py — thick
class ChatService:
    async def process(self, request: ChatRequest) -> ChatResponse:
        intent, context = await asyncio.gather(
            self.router_ai.classify(request.message),
            self.pinecone.search(request.message, request.user_id),
        )
        if intent.requires_list:
            was_data = await self.was_client.get_list(request.user_id, intent.list_type)
        else:
            was_data = None
        return await self.gemini.generate(intent.mode, context, was_data, request)
```

### Pattern 2: Parallel I/O with asyncio.gather

**What:** Fire multiple independent async calls simultaneously and await all results together.
**When to use:** /ai-chat requires both Router AI intent classification AND Pinecone context search — these are independent and should run in parallel.
**Trade-offs:** Slightly more complex error handling (one failure cancels both), but latency cut roughly in half vs sequential.

**Example:**
```python
intent, context = await asyncio.gather(
    self.router_ai.classify(message),
    self.pinecone.search(message, user_id),
)
```

### Pattern 3: Post-Response Background Summary

**What:** After returning a response to the WAS, trigger an async pipeline: LLM summarizes the interaction → local embedding → Pinecone upsert. Uses FastAPI's `BackgroundTasks`.
**When to use:** Memory accumulation that must not block user-facing latency. The user gets their answer; memory storage is fire-and-forget.
**Trade-offs:** Background task runs in the same process. If the task fails, it fails silently unless logged explicitly. For a capstone project, BackgroundTasks is sufficient — Celery/RQ is overkill here.

**Example:**
```python
# services/background_summary.py
async def run(request: ChatRequest, result: ChatResponse, pinecone: PineconeClient):
    try:
        summary = await gemini.summarize(request, result)
        vector = embedding_service.encode(summary)
        await pinecone.upsert(user_id=request.user_id, vector=vector, metadata={...})
    except Exception as e:
        logger.error(f"Background summary failed: {e}")
```

### Pattern 4: Dependency Injection for External Clients

**What:** Clients (Gemini, Pinecone, httpx WAS) are created once at startup and injected via FastAPI's dependency system — not instantiated inside handlers.
**When to use:** Always, for any stateful client (connection pool, API credentials, rate limiters).
**Trade-offs:** Slightly more boilerplate in `dependencies.py`, but enables clean testing via dependency overrides and prevents connection proliferation.

**Example:**
```python
# dependencies.py
_pinecone_client: PineconeClient | None = None

def get_pinecone_client() -> PineconeClient:
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient(settings.pinecone_api_key, settings.pinecone_index)
    return _pinecone_client
```

## Data Flow

### /process-meal Flow

```
WAS → POST /process-meal
    ↓
[Router] validate input → [MealService]
    ↓
PineconeClient.search(meal_text, user_id) → top-k meal context vectors
    ↓
GeminiClient.analyze_meal(meal_data, context) → calorie + nutrition analysis
    ↓
[Router] return MealResponse to WAS
    ↓ (background, non-blocking)
BackgroundSummary.run(request, result) → LLM summary → embed → Pinecone upsert
```

### /recommend Flow

```
WAS → POST /recommend
    ↓
[Router] validate input → [RecommendService]
    ↓
PineconeClient.search(user_profile + goal, user_id) → relevant past context
    ↓
GeminiClient.recommend(profile, context) → exercise/diet plan
    ↓
[Router] return RecommendResponse to WAS
    ↓ (background)
BackgroundSummary.run(request, result) → LLM summary → embed → Pinecone upsert
```

### /ai-chat Flow (most complex)

```
WAS → POST /ai-chat
    ↓
[Router] validate input → [ChatService]
    ↓
asyncio.gather([
    RouterAI.classify(message)      → intent (mode 1-8, requires_list flag),
    PineconeClient.search(message)  → top-k context vectors
])
    ↓
if intent.requires_list:
    WASClient.get_list(user_id, list_type) → current exercise/diet list
    ↓
GeminiClient.generate(mode, context, was_data, message)
    → structured response (mode-specific schema)
    ↓
[Router] return ChatResponse to WAS
    ↓ (background)
BackgroundSummary.run(request, result) → LLM summary → embed → Pinecone upsert
```

### Key Data Flows Summary

1. **Inbound (WAS → FastAPI):** JSON over HTTP POST. Validated by Pydantic schemas at router boundary. Services receive typed domain objects, not raw dicts.
2. **Retrieval (FastAPI → Pinecone):** Text query → local embedding → Pinecone similarity search → list of Document objects with metadata.
3. **Generation (FastAPI → Gemini):** Structured prompt (system + context + user message) → Gemini Flash → structured text parsed to Pydantic response model.
4. **Conditional WAS call (FastAPI → WAS):** httpx async GET with user_id and list_type → JSON list returned synchronously within the request pipeline.
5. **Memory write (Background → Pinecone):** Conversation pair → LLM summary text → local embedding → Pinecone upsert with user_id namespace.

## Component Boundaries

| Boundary | Direction | Protocol | Notes |
|----------|-----------|----------|-------|
| WAS ↔ FastAPI Hub | Bidirectional | HTTP REST (sync) | FastAPI is always the server here; WAS calls FastAPI. FastAPI calls WAS only for list data in /ai-chat |
| FastAPI Hub → Pinecone | Outbound | HTTPS (Pinecone SDK) | Use async Pinecone SDK (PineconeAsyncio) to avoid blocking event loop |
| FastAPI Hub → Gemini Flash | Outbound | HTTPS (Google AI SDK) | Async calls; rate-limit awareness needed |
| FastAPI Hub → Router AI | Internal or Outbound | Function call or HTTPS | If Router AI is a separate Gemini call, it's outbound; if it's a local classifier model, it's an internal call |
| Background → Pinecone | Outbound (async) | HTTPS | Runs after response is sent; must handle failures gracefully with logging |

## Suggested Build Order

Build in this dependency order — each phase is unblocked only after the previous completes:

1. **Foundation** — `app/main.py`, `app/config.py`, `app/core/` (logging, exceptions), `.env` setup. No external calls yet.
2. **Schemas** — All Pydantic request/response models. Defines the contract that all other layers depend on.
3. **Clients** — `PineconeClient`, `GeminiClient`, `WASClient`, `RouterAI`. Each independently testable with mocked SDKs.
4. **Core Embedding** — `core/embedding.py`. Needed by PineconeClient and BackgroundSummary.
5. **Services** — `MealService`, `RecommendService` (simpler, no parallel flow). Then `ChatService` (complex parallel + conditional).
6. **Background Summary** — `services/background_summary.py`. Depends on GeminiClient + PineconeClient + EmbeddingService.
7. **Routers** — Wire services and BackgroundTasks into HTTP endpoints. System is now runnable end-to-end.
8. **Integration tests** — Test each endpoint against mocked external services.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Capstone / 0-100 users | Current design is correct. BackgroundTasks is sufficient. Single Uvicorn process. |
| 100-1k concurrent users | Add Gunicorn with multiple Uvicorn workers. Keep BackgroundTasks. Monitor Gemini rate limits. |
| 1k+ users | Replace BackgroundTasks with Celery + Redis for retry-capable memory writes. Add response caching for repeated queries (Redis semantic cache). Consider Pinecone namespace sharding per user cohort. |

### Scaling Priorities

1. **First bottleneck:** Gemini Flash API rate limits and latency under concurrent load. Fix: response caching for identical or near-identical queries.
2. **Second bottleneck:** BackgroundTasks piling up if Pinecone writes are slow. Fix: migrate to Celery worker pool with bounded queue.

## Anti-Patterns

### Anti-Pattern 1: Business Logic in Routers

**What people do:** Write orchestration logic (VDB search + LLM call + response build) directly inside the route function.
**Why it's wrong:** Untestable without HTTP, bloated router files, impossible to reuse logic across endpoints.
**Do this instead:** Router calls one service method. Service owns all coordination.

### Anti-Pattern 2: Synchronous SDK Calls in Async Handlers

**What people do:** Use the Pinecone or Gemini SDK's synchronous methods inside `async def` route handlers.
**Why it's wrong:** Blocks the entire event loop; every concurrent request queues behind the blocking call. Kills throughput.
**Do this instead:** Use async SDK variants (Pinecone's `PineconeAsyncio`, Google AI SDK's async methods, `httpx.AsyncClient`). If a library has no async version, use `asyncio.to_thread()`.

### Anti-Pattern 3: Global Client Instantiation in Module Scope

**What people do:** Instantiate `PineconeClient()` or `httpx.Client()` at module import time.
**Why it's wrong:** Connections open at import time (slow startup, leaks in tests), impossible to override in tests, API keys read before settings are validated.
**Do this instead:** Use FastAPI lifespan event or lazy singleton via `Depends()` in `dependencies.py`.

### Anti-Pattern 4: Swallowed Background Task Failures

**What people do:** Wrap background task in a bare `try/except Exception: pass`.
**Why it's wrong:** Memory writes silently fail — the system appears healthy but the vector DB progressively loses context data without any signal.
**Do this instead:** Log all exceptions with full context (`logger.exception()`). Add a counter or health metric for failed background writes.

### Anti-Pattern 5: Monolithic GeminiClient with Hardcoded Prompts

**What people do:** Put all 8 chat modes as if/elif branches with hardcoded prompt strings inside the route handler or a single 400-line client method.
**Why it's wrong:** Adding a 9th mode requires modifying the existing file, violating open/closed. Prompts become untestable.
**Do this instead:** Define mode-specific prompt builders as separate functions or a strategy pattern. Each mode's prompt is independently testable.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Gemini Flash (Google AI) | `google-generativeai` SDK, async calls | Use `gemini-2.0-flash` model; rate limits apply; structured output via response schema |
| Pinecone | `pinecone` SDK v3+ with `PineconeAsyncio` | Cloud-managed index; use namespaces per user_id for isolation; upsert batch size matters |
| Node.js WAS | `httpx.AsyncClient` HTTP GET | Only called from ChatService when intent.requires_list is True; keep timeout short (2-3s) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| api/ ↔ services/ | Direct async function call via DI | Services injected via `Depends()`; router does not import service classes directly |
| services/ ↔ clients/ | Direct async function call via DI | Clients injected into services via constructor or `Depends()` |
| services/ → background_summary | FastAPI BackgroundTasks | One-way; response already sent; background gets copies of request/result data |
| core/embedding ↔ clients/pinecone | Function call | Pinecone client calls embedding service to convert text before upsert/search |

## Sources

- [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — project structure, domain-based layout (MEDIUM confidence — community guide, widely adopted)
- [Building LLM apps with FastAPI — Agents Arcade](https://agentsarcade.com/blog/building-llm-apps-with-fastapi-best-practices) — thin routers, background task patterns (MEDIUM confidence)
- [FastAPI Background Tasks — Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) — BackgroundTasks mechanics and limitations (HIGH confidence)
- [Building production-ready AI agents with RAG and FastAPI — The New Stack](https://thenewstack.io/how-to-build-production-ready-ai-agents-with-rag-and-fastapi/) — RAG pipeline component structure (MEDIUM confidence)
- [Building a RAG Router in 2025 — Medium](https://medium.com/@tim_pearce/building-a-rag-router-in-2025-e0e9d99efe44) — intent routing patterns (MEDIUM confidence)
- [Pinecone 2025 Release Notes](https://docs.pinecone.io/release-notes/2025) — PineconeAsyncio client availability (HIGH confidence)
- [FastAPI + Celery background tasks — TestDriven.io](https://testdriven.io/blog/fastapi-and-celery/) — when to use BackgroundTasks vs Celery (HIGH confidence)

---
*Architecture research for: FastAPI AI Orchestration Hub (Health/Exercise RAG + LLM)*
*Researched: 2026-03-21*
