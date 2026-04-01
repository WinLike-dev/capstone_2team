# Stack Research

**Domain:** FastAPI AI Orchestration Hub — Health/Exercise recommendation service
**Researched:** 2026-03-21
**Confidence:** HIGH (all core library versions verified against PyPI as of 2026-03-21)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.135.1 | ASGI web framework, REST API server | Async-native, OpenAPI auto-generation, Pydantic v2 integration, the de-facto standard for Python AI services in 2025. Pydantic v2 JSON serialization uses Rust, giving 2x+ throughput over Flask/Django for I/O-bound AI workloads. |
| Pydantic | 2.12.5 | Request/response schema validation, structured output modeling | Required by FastAPI. V2 rewrote core in Rust. Enables strict typing for Gemini structured output schemas and Pinecone record models. Do not downgrade to v1 — support is deprecated in FastAPI. |
| Uvicorn | 0.42.0 | ASGI server (development + production) | Standard ASGI server for FastAPI. Single-process with `--reload` for dev; add Gunicorn workers in production (see deployment section). Requires Python 3.10+. |
| google-genai | 1.68.0 | Gemini Flash LLM API client | This is the new, GA-stable Google Gen AI SDK (`pip install google-genai`). Replaces the deprecated `google-generativeai` package (support ended November 2025). Supports async via `aiohttp` extra, structured output via response schema, and function calling. |
| pinecone | 8.1.0 | Vector DB client for Pinecone Cloud | Current official SDK. As of v6+, ships `PineconeAsyncio` / `IndexAsyncio` for full asyncio-native usage — no thread pool hacks. Install as `pinecone[asyncio]`. Vector search + upsert without blocking the event loop. |
| sentence-transformers | 5.3.0 | Local embedding generation | Runs entirely within FastAPI process — zero external API call for embeddings. Models like `all-MiniLM-L6-v2` (384-dim, fast CPU) or `paraphrase-multilingual-MiniLM-L12-v2` (Korean+English support, critical for this health/exercise domain with Korean user data). Choose based on language coverage needed. |
| pydantic-settings | 2.13.1 | Environment variable / secrets management | Standard FastAPI config pattern. `BaseSettings` + `.env` file + `@lru_cache` gives type-safe config with load priority: env vars > .env > defaults. Replaces raw `python-dotenv` usage for structured config. |
| httpx | 0.28.1 | Async HTTP client for outbound calls to Node.js WAS | Required for the conditional flow in `/ai-chat` where FastAPI calls back to Node.js WAS for user data lists. The async `AsyncClient` integrates with FastAPI's event loop. Use lifespan context to create one client instance (connection pooling). |
| python-dotenv | 1.2.2 | `.env` file loading (used by pydantic-settings) | pydantic-settings depends on it for `.env` parsing. Install alongside pydantic-settings. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| gunicorn | latest stable (~23.x) | Multi-process production server manager | Production deployment only. Spawn Uvicorn workers: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`. Not needed in development or single-container capstone deploy. |
| torch | latest stable (~2.6) | PyTorch runtime for sentence-transformers | Required by sentence-transformers for model inference. CPU-only mode is fine for this scale: `pip install torch --index-url https://download.pytorch.org/whl/cpu`. Do not install GPU variant unless you have CUDA — it is 3GB+ and unnecessary for capstone. |
| transformers | latest stable (~4.50) | HuggingFace model loading (sentence-transformers dependency) | Pulled in automatically by sentence-transformers. Pinned to compatible version by sentence-transformers itself — do not pin separately. |
| pytest | latest stable (~8.x) | Unit and integration testing | All test files. Pair with `pytest-asyncio` for testing async FastAPI routes and background tasks. |
| pytest-asyncio | latest stable (~0.25) | Async test support | Required for `async def` test functions that test FastAPI endpoints and async service methods. |
| httpx (test client) | same as above | FastAPI `TestClient` replacement for async tests | Use `httpx.AsyncClient(app=app)` in tests — the synchronous `TestClient` blocks and can deadlock async routes. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uvicorn with `--reload` | Hot reload during development | `uvicorn app.main:app --reload --port 8000`. Do not use `--reload` in production. |
| python-dotenv `.env` file | Local secrets management | Never commit `.env`. Add to `.gitignore` immediately. Use `.env.example` with placeholder values in the repo. |
| pydantic model `model_json_schema()` | Auto-generate JSON schema for Gemini structured output | Pass `MyResponseModel.model_json_schema()` as the `response_schema` to Gemini. Keeps schema definition in one place. |

---

## Installation

```bash
# Core runtime
pip install fastapi==0.135.1
pip install uvicorn==0.42.0
pip install pydantic==2.12.5
pip install pydantic-settings==2.13.1
pip install python-dotenv==1.2.2

# AI / LLM
pip install "google-genai[aiohttp]==1.68.0"

# Vector DB
pip install "pinecone[asyncio]==8.1.0"

# Embeddings (CPU-only torch to minimize image size)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==5.3.0

# Outbound HTTP (Node.js WAS calls)
pip install httpx==0.28.1

# Dev / testing
pip install pytest pytest-asyncio
```

Full `requirements.txt`:
```
fastapi==0.135.1
uvicorn==0.42.0
pydantic==2.12.5
pydantic-settings==2.13.1
python-dotenv==1.2.2
google-genai==1.68.0
pinecone==8.1.0
sentence-transformers==5.3.0
httpx==0.28.1
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `google-genai` (new SDK) | `google-generativeai` (legacy) | Never — legacy support ended November 2025. All new code must use `google-genai`. |
| `pinecone[asyncio]` with `PineconeAsyncio` | `pinecone` with `run_in_threadpool` | Only if you are on Pinecone SDK < v6 (do not do this — upgrade). |
| `sentence-transformers` (self-hosted) | Google `text-embedding-004` via API | Use Google Embedding API if you need to minimize server memory/compute and are okay with per-call latency + API cost. For this project, `sentence-transformers` avoids external API dependency for background embedding — right call given the "FastAPI owns embedding" constraint. |
| `sentence-transformers` (self-hosted) | Pinecone's built-in embedding models | Use Pinecone built-in embedding if you configure an integrated index (Pinecone manages embedding). Not chosen here because the project explicitly generates embeddings in FastAPI before upserting. |
| FastAPI `BackgroundTasks` | Celery + Redis | Use Celery only if you need distributed workers, task retry UI, or task result persistence. For this project, background summary (LLM summarize → embed → Pinecone upsert) is fire-and-forget and runs within the same process — `BackgroundTasks` is the right fit. |
| FastAPI `BackgroundTasks` | ARQ + Redis | Use ARQ if tasks must survive server restart or need status polling. Not required for this project's v1 scope. |
| `httpx.AsyncClient` | `aiohttp` | Both work. `httpx` is the FastAPI ecosystem default (installed as a FastAPI dependency already), has a cleaner API, and is the recommended choice in FastAPI docs. |
| `asyncio.gather()` for parallel ops | Sequential awaits | Use `asyncio.gather()` for the `/ai-chat` endpoint's parallel Router AI + Vector DB search — confirmed 66% latency reduction in async LLM pipelines. Do not await them sequentially. |
| Pydantic v2 `BaseModel` | dataclasses or TypedDict | Pydantic v2 handles validation, serialization, and JSON schema generation in one place. Required for Gemini structured output schema generation. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `google-generativeai` package | Support permanently ended November 2025. No security patches, no new models, no async support. | `google-genai` (package name is `google-genai`, import is `from google import genai`) |
| `pinecone-client` package | Renamed to `pinecone` in v5.1.0. `pinecone-client` on PyPI is stale. | `pinecone` package |
| Synchronous `requests` library | Blocks the event loop in async FastAPI. Under load, a single blocking call stalls ALL concurrent requests. | `httpx.AsyncClient` |
| `run_in_threadpool` for Pinecone calls | Workaround for old Pinecone SDK. SDK v6+ has native async — wrapping in threadpool wastes resources. | `PineconeAsyncio` / `IndexAsyncio` directly |
| Loading sentence-transformers model per-request | Model load takes 1-5 seconds. Doing this inside a route handler kills latency. | Load model once at app startup using FastAPI lifespan event, store in app state. |
| Sequential LLM + Vector DB calls in `/ai-chat` | Router AI and Vector DB search are independent. Sequential doubles latency (~2s → ~1s). | `asyncio.gather(router_classify(), vector_search())` |
| Pydantic v1 | Deprecated in FastAPI, significantly slower (pure Python), will be removed in a future FastAPI version. | Pydantic v2 (already the default) |
| `flask` or `django` for this service | Sync-first frameworks. Using them for an async-heavy AI orchestration service requires threading hacks and loses most performance benefits. | FastAPI |

---

## Stack Patterns by Variant

**If embedding model must support Korean text (likely — this is a Korean health service):**
- Use `paraphrase-multilingual-MiniLM-L12-v2` (768-dim) instead of `all-MiniLM-L6-v2` (384-dim, English-optimized)
- Pinecone index dimension must match: set `dimension=768` for multilingual model
- Test both: multilingual adds ~50ms inference time on CPU vs English-only model

**If deployment is a single Docker container (capstone typical setup):**
- Use `uvicorn` directly, no Gunicorn
- Single-process is fine for capstone scale
- `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

**If Gemini API rate limits become an issue under testing:**
- Add `asyncio.Semaphore` around Gemini calls to cap concurrent requests
- Pattern: `async with semaphore: response = await client.aio.models.generate_content(...)`

**If background summary tasks become slow or back up:**
- Migrate from `BackgroundTasks` to ARQ + Redis as a drop-in upgrade path
- Keep the same service function signatures — only the task dispatch changes

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `fastapi==0.135.1` | `pydantic>=2.0.0` | FastAPI dropped Pydantic v1 support. Do not mix. |
| `pinecone==8.1.0` | Python 3.10+ | SDK requires Python 3.10 or greater (tested up to 3.13). |
| `sentence-transformers==5.3.0` | `torch>=2.0`, `transformers>=4.41` | sentence-transformers pulls compatible torch/transformers versions automatically. Let pip resolve — do not pin torch separately unless you need CPU-only build. |
| `google-genai==1.68.0` | Python 3.9+ | Async support requires `google-genai[aiohttp]` extra. |
| `uvicorn==0.42.0` | Python 3.10+ | Requires Python 3.10+. Check deployment environment. |
| `pydantic-settings==2.13.1` | `pydantic>=2.7.0` | Requires Pydantic v2. Do not install with Pydantic v1. |

---

## Sources

- PyPI `fastapi` — version 0.135.1, verified 2026-03-21: https://pypi.org/project/fastapi/
- PyPI `google-genai` — version 1.68.0, verified 2026-03-21: https://pypi.org/project/google-genai/
- PyPI `pinecone` — version 8.1.0, verified 2026-03-21: https://pypi.org/project/pinecone/
- PyPI `sentence-transformers` — version 5.3.0, verified 2026-03-21: https://pypi.org/project/sentence-transformers/
- PyPI `httpx` — version 0.28.1, verified 2026-03-21: https://pypi.org/project/httpx/
- PyPI `pydantic` — version 2.12.5, verified 2026-03-21: https://pypi.org/project/pydantic/
- PyPI `pydantic-settings` — version 2.13.1, verified 2026-03-21: https://pypi.org/project/pydantic-settings/
- PyPI `uvicorn` — version 0.42.0, verified 2026-03-21: https://pypi.org/project/uvicorn/
- Pinecone async FastAPI official example: https://github.com/pinecone-io/fastapi-pinecone-async-example
- Pinecone PineconeAsyncio docs: https://sdk.pinecone.io/python/asyncio.html
- Google Gemini API libraries (new SDK announcement): https://ai.google.dev/gemini-api/docs/libraries
- FastAPI BackgroundTasks vs ARQ comparison (MEDIUM confidence — WebSearch): https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/
- FastAPI production deployment with Uvicorn/Gunicorn (MEDIUM confidence — WebSearch): https://blog.greeden.me/en/2025/09/02/the-definitive-guide-to-fastapi-production-deployment-with-dockeryour-one-stop-reference-for-uvicorn-gunicorn-nginx-https-health-checks-and-observability-2025-edition/

---
*Stack research for: FastAPI AI Orchestration Hub (Health/Exercise domain)*
*Researched: 2026-03-21*
