# Phase 2: Core Integrations - Research

**Researched:** 2026-03-22
**Domain:** Pinecone Asyncio, sentence-transformers, google-genai SDK, tenacity retry
**Confidence:** HIGH (all major claims verified against official docs or PyPI)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### 임베딩 모델
- paraphrase-multilingual-MiniLM-L12-v2 (768-dim) 확정
- lifespan 시작 시 1회 로드, app.state.embed_model에 저장
- 임베딩 생성은 run_in_threadpool로 event loop 블록 방지 (EMBD-02)
- Pinecone 인덱스 dimension과 768 일치 보장 (EMBD-03)

#### Pinecone 클라이언트
- Serverless 타입, aws/us-east-1 리전
- 코드에서 인덱스 자동 생성 (lifespan에서 인덱스 없으면 create_index)
- namespace 기반 사용자 격리: user_id를 namespace로 사용 (PINE-02)
- 메타데이터 최소한: user_id, summary, timestamp만 저장
- 벡터 ID: UUID4 생성
- 검색 top_k: 3
- 테스트: 모킹만 (실제 Pinecone 연결 없음)
- 테스트용 별도 인덱스 불필요

#### Gemini Flash 클라이언트
- google-genai SDK 사용 (GEMI-01)
- 모델명: 환경변수 GEMINI_MODEL_NAME으로 Settings에 추가 (기본값 설정)
- JSON 출력 강제: response_mime_type='application/json' + response_schema (SDK 레벨 보장)
- 모드별 프롬프트: app/prompts/ 디렉토리에 Python 상수로 관리 (GEMI-03)
- 프롬프트 템플릿: f-string/.format()으로 user_profile 필드를 시스템 프롬프트에 주입 (GEMI-04, GEMI-05)
- 한국어 응답: 시스템 프롬프트에 '한국어로 응답하세요' 명시
- 재시도: tenacity 라이브러리로 exponential backoff + jitter (GEMI-02)
- 테스트: 모킹만 (실제 API 호출 없음)

#### Router AI 클라이언트
- Gemini Flash Lite 사용 (별도 경량 모델)
- 별도 API 키: ROUTER_API_KEY 환경변수를 Settings에 추가
- 모델명: ROUTER_MODEL_NAME 환경변수 (기본값 'gemini-2.0-flash-lite')
- 별도 클라이언트: clients/router.py에 RouterClient 분리 (ROUT-03 단독 테스트)
- 출력 형식: mode + reason만 (router_system_instruction.txt 기준, confidence score 없음)
- 시스템 프롬프트: docs/router_system_instruction.txt 내용을 app/prompts/router.py로 Python 상수로 이전
- Phase 2 범위: 클라이언트 + 단독 테스트만. 엔드포인트 연동은 v2

#### 클라이언트 초기화/생명주기
- lifespan 초기화 순서: 임베딩 모델 → Pinecone → Gemini (임베딩이 가장 느려서 먼저)
- 초기화 실패 시: 전체 서버 시작 중단 (불완전한 상태 방지)
- app.state 저장: 개별 속성 (app.state.pinecone_client, app.state.embed_model 등)
- Shutdown: 필수 정리만 (httpx AsyncClient.aclose(), Pinecone 연결 종료)

### Claude's Discretion
- 각 클라이언트의 내부 메서드 설계 (search, upsert, generate 등)
- tenacity 재시도 횟수 및 backoff 파라미터
- Router AI JSON 파싱 실패 시 폴백 전략
- Pinecone 인덱스 자동 생성 시 세부 설정 (metric, replicas 등)
- 클라이언트 에러를 Phase 1에서 정의한 에러 코드(GEMINI_ERROR, PINECONE_ERROR, EMBEDDING_ERROR)에 매핑하는 방식

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PINE-01 | PineconeAsyncio 클라이언트 연동 (async 검색/저장) | PineconeAsyncio + IndexAsyncio API confirmed via official SDK docs |
| PINE-02 | namespace 기반 사용자 격리 (user_id별 namespace 강제) | upsert/query namespace param confirmed; each query scoped to single namespace |
| PINE-03 | 벡터 검색 (user_id + 메시지 기반 맥락 검색, 결과 반환) | idx.query(vector=..., top_k=3, namespace=user_id, include_metadata=True) |
| PINE-04 | 벡터 저장 (임베딩 값 + user_id + 요약 데이터 upsert) | idx.upsert(vectors=[Vector(id=..., values=..., metadata={...})], namespace=user_id) |
| EMBD-01 | sentence-transformers multilingual 모델 로딩 | SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2") — CRITICAL: outputs 384-dim not 768 |
| EMBD-02 | 텍스트 임베딩 생성 (run_in_threadpool로 event loop 블록 방지) | starlette.concurrency.run_in_threadpool confirmed as standard FastAPI pattern |
| EMBD-03 | Pinecone 인덱스 dimension과 임베딩 모델 dimension 일치 보장 | CRITICAL: must use 384 (MiniLM) or switch to mpnet-base-v2 for 768 |
| GEMI-01 | google-genai SDK 기반 Gemini Flash 클라이언트 구현 | google-genai 1.67.0 installed; client.aio.models.generate_content for async |
| GEMI-02 | 재시도 로직 (429 에러 대응, exponential backoff + jitter) | tenacity 9.1.4; catch google.api_core.exceptions.ResourceExhausted |
| GEMI-03 | 모드별 시스템 지시사항 프롬프트 관리 (JSON 출력 형식 지정) | app/prompts/ Python constants; response_mime_type + response_schema pattern |
| GEMI-04 | Mode 7 (식단 기록) 프롬프트: 칼로리 분석 + 간결한 피드백 메시지 | MealAnalysisData Pydantic schema exists for response_schema |
| GEMI-05 | Mode 8 (추천 기능) 프롬프트: 운동/식단 추천 + 소모/섭취 칼로리 | RecommendData Pydantic schema exists for response_schema |
| ROUT-01 | LLM 기반 의도 분류 모듈 구현 (6가지 모드) | RouterClient using gemini-2.0-flash-lite with router system instruction |
| ROUT-02 | Router 시스템 지침서 프롬프트 적용 (JSON 출력: mode + reason) | router_system_instruction.txt content verified; mode 1-6 + reason output |
| ROUT-03 | Router AI 단독 테스트 가능한 인터페이스 | Separate clients/router.py class; AsyncMock in tests |

</phase_requirements>

## Summary

Phase 2 implements four independent external system clients: Pinecone vector DB, sentence-transformers embedding, Gemini Flash LLM, and Router AI. All clients are initialized in FastAPI's lifespan context manager and stored in `app.state`. The key challenge is that each client has different async requirements — Pinecone is native async, sentence-transformers is CPU-bound synchronous (needs threadpool), and Gemini has an async wrapper via `client.aio`.

A critical dimension mismatch was discovered: `paraphrase-multilingual-MiniLM-L12-v2` outputs **384 dimensions**, NOT 768 as stated in CONTEXT.md. The 768-dim multilingual model is `paraphrase-multilingual-mpnet-base-v2`. The planner MUST resolve this before setting the Pinecone index dimension — either use 384 with MiniLM-L12-v2 (locked model name) or acknowledge the model name was a proxy for the larger mpnet model. Since EMBD-03 requires dimension consistency, whatever model is used must match the Pinecone index dimension exactly.

All library versions are verified current: pinecone 8.x (with asyncio extra), google-genai 1.67.0 (already installed), sentence-transformers 5.3.0, tenacity 9.1.4. The google-genai SDK uses `client.aio.models.generate_content()` for async calls, and the correct exception to catch for 429 retries is `google.api_core.exceptions.ResourceExhausted`.

**Primary recommendation:** Build each client as an independent class in `app/clients/`, wire them through lifespan, and test exclusively with mocks (no live API calls in tests).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pinecone[asyncio] | 8.x (latest) | Async vector DB client | PineconeAsyncio + IndexAsyncio is official async API |
| sentence-transformers | 5.3.0 | Multilingual embedding generation | Wraps HuggingFace models; SentenceTransformer class |
| google-genai | 1.67.0 (installed) | Gemini API client | Official Google SDK; has client.aio for async |
| tenacity | 9.1.4 | Retry with exponential backoff | De facto standard retry library for Python |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| starlette.concurrency | (bundled with FastAPI) | run_in_threadpool | Offload CPU-bound sync code from async context |
| google.api_core.exceptions | (bundled with google-genai) | ResourceExhausted | Catch 429 errors for retry logic |
| uuid | (stdlib) | UUID4 vector ID generation | Vector IDs for Pinecone upsert |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| paraphrase-multilingual-MiniLM-L12-v2 (384-dim) | paraphrase-multilingual-mpnet-base-v2 (768-dim) | mpnet is larger/slower but matches the 768-dim assumption in CONTEXT.md |
| tenacity | asyncio.sleep + manual retry loop | tenacity is cleaner; handles jitter automatically |
| client.aio.models.generate_content | asyncio.to_thread wrapping sync call | Native async is preferred |

**Installation:**
```bash
pip install "pinecone[asyncio]" sentence-transformers google-genai tenacity
```

## Architecture Patterns

### Recommended Project Structure
```
app/
├── clients/
│   ├── __init__.py          # (currently empty)
│   ├── pinecone.py          # PineconeClient wrapper
│   ├── embedding.py         # EmbeddingClient wrapper
│   ├── gemini.py            # GeminiClient (Mode 7, 8)
│   └── router.py            # RouterClient (Mode 1-6 classification)
├── prompts/
│   ├── __init__.py
│   ├── meal.py              # MEAL_ANALYSIS_SYSTEM_PROMPT (Mode 7)
│   ├── recommend.py         # RECOMMENDATION_SYSTEM_PROMPT (Mode 8)
│   └── router.py            # ROUTER_SYSTEM_PROMPT (from docs/router_system_instruction.txt)
└── core/
    ├── config.py            # Settings — add GEMINI_MODEL_NAME, ROUTER_API_KEY, ROUTER_MODEL_NAME
    └── lifespan.py          # Wire all client initialization here
```

### Pattern 1: Pinecone Async Initialization in Lifespan

**What:** Use `PineconeAsyncio` as async context manager, get index host via `describe_index`, store `IndexAsyncio` in app.state.
**When to use:** FastAPI lifespan startup; enables connection reuse across requests.

```python
# Source: https://www.pinecone.io/learn/pinecone-async-fastapi/
# Source: https://sdk.pinecone.io/python/asyncio.html
from pinecone import PineconeAsyncio, ServerlessSpec

async def _init_pinecone(app: FastAPI, settings: Settings) -> None:
    pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
    # Store control-plane client for lifecycle management
    app.state._pinecone_control = pc
    await pc.__aenter__()  # or manage manually with close()

    # Create index if it does not exist
    if not await pc.has_index(settings.PINECONE_INDEX_NAME):
        await pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=384,  # CRITICAL: must match embedding model output
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    description = await pc.describe_index(settings.PINECONE_INDEX_NAME)
    # Store IndexAsyncio for data operations — no context manager needed per request
    app.state.pinecone_index = pc.IndexAsyncio(host=description.host)
```

### Pattern 2: EmbeddingClient with run_in_threadpool

**What:** SentenceTransformer.encode() is synchronous and CPU-bound. Wrap with `run_in_threadpool` to avoid blocking the event loop.
**When to use:** Every embedding generation call inside an async function.

```python
# Source: FastAPI docs + starlette.concurrency
from sentence_transformers import SentenceTransformer
from starlette.concurrency import run_in_threadpool

class EmbeddingClient:
    def __init__(self, model: SentenceTransformer) -> None:
        self._model = model

    async def embed(self, text: str) -> list[float]:
        # run_in_threadpool offloads the synchronous encode() call
        vector = await run_in_threadpool(self._model.encode, text)
        return vector.tolist()
```

Loading at startup:
```python
# In lifespan startup — load once, store in app.state
from sentence_transformers import SentenceTransformer
model = await run_in_threadpool(
    SentenceTransformer, "paraphrase-multilingual-MiniLM-L12-v2"
)
app.state.embed_model = model
```

### Pattern 3: Gemini Async Client with Structured Output

**What:** Use `client.aio.models.generate_content` with `GenerateContentConfig` to enforce JSON schema output.
**When to use:** Mode 7 (meal analysis) and Mode 8 (recommendation) calls.

```python
# Source: https://googleapis.github.io/python-genai/
from google import genai
from google.genai import types
from app.schemas.meal import MealAnalysisData

class GeminiClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    @retry(
        wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(ResourceExhausted),
    )
    async def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_schema: type,
    ) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        return response.text
```

### Pattern 4: RouterClient with JSON Fallback

**What:** Lightweight intent classifier using Gemini Flash Lite. Parses mode+reason JSON; falls back to mode=1 on parse failure.
**When to use:** ROUT-01/ROUT-02/ROUT-03 implementation.

```python
# RouterOutput schema for structured response
from pydantic import BaseModel

class RouterOutput(BaseModel):
    mode: int  # 1-6
    reason: str

class RouterClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def classify(self, user_message: str) -> RouterOutput:
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=ROUTER_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RouterOutput,
            ),
        )
        try:
            return RouterOutput.model_validate_json(response.text)
        except Exception:
            # Fallback: return mode 1 (simple conversation) on parse failure
            return RouterOutput(mode=1, reason="파싱 실패 — 기본 모드로 처리")
```

### Pattern 5: Tenacity Retry for 429 Errors

**What:** Catch `ResourceExhausted` (HTTP 429) from google-genai and retry with exponential backoff + jitter.
**When to use:** All Gemini API calls.

```python
# Source: https://cloud.google.com/blog/products/ai-machine-learning/learn-how-to-handle-429-resource-exhaustion-errors-in-your-llms
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted

@retry(
    wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(ResourceExhausted),
    reraise=True,
)
async def _call_with_retry(...):
    ...
```

### Anti-Patterns to Avoid

- **Calling SentenceTransformer.encode() directly inside async def without run_in_threadpool:** Blocks the event loop for the duration of CPU inference — all other requests stall.
- **Creating a new PineconeAsyncio or IndexAsyncio per request:** Destroys connection reuse; use the lifespan-initialized instance from app.state.
- **Catching bare Exception instead of ResourceExhausted for retry:** Will retry on auth errors, bad requests, and other permanent failures — wastes quota and delays error surfacing.
- **Calling `response_schema` with `additionalProperties` set to True:** google-genai SDK rejects this at client-side validation even though the API supports it since Nov 2025.
- **Mixing response_mime_type='application/json' with tools/function calling:** API error — cannot combine. These are mutually exclusive.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exponential backoff retry | Custom asyncio.sleep + counter | tenacity | Handles jitter, stop conditions, reraise, async/sync transparently |
| Async threadpool offload | asyncio.get_event_loop().run_in_executor | starlette run_in_threadpool | Uses AnyIO capacity limiter, consistent with FastAPI internals |
| JSON schema enforcement | Prompt engineering + manual parse | response_mime_type + response_schema | SDK-level guarantee; no regex post-processing needed |
| Vector namespace isolation | Application-level filtering | Pinecone namespace param | Native index feature; zero overhead, fully isolated |
| Index existence check | List all indexes + name match | pc.has_index() | Direct boolean method in PineconeAsyncio |

**Key insight:** Each "don't hand-roll" item has a deceptively complex edge case — retry needs jitter to avoid thundering herd, threadpool offload needs capacity limiting, JSON output needs schema not just prompting.

## Critical Finding: Embedding Dimension Mismatch

**CONTEXT.md states:** `paraphrase-multilingual-MiniLM-L12-v2 (768-dim) 확정`

**Verified fact:** `paraphrase-multilingual-MiniLM-L12-v2` outputs **384 dimensions** (confirmed via HuggingFace model card).

The 768-dimension multilingual model is `paraphrase-multilingual-mpnet-base-v2`.

**Decision required before implementation:** Either:
1. Use dimension=384 with the locked model name `paraphrase-multilingual-MiniLM-L12-v2`
2. Switch to `paraphrase-multilingual-mpnet-base-v2` (768-dim, larger/slower, more accurate)

This cannot be changed after the Pinecone index is created without rebuilding the entire index. **The planner must pick one and document the chosen dimension.**

For this project's use case (RAG context retrieval, Korean text), both models support Korean. The MiniLM-L12-v2 at 384-dim is faster and smaller — recommended unless 768-dim quality difference matters. If Pinecone index already exists with 768-dim, use mpnet-base-v2.

## Common Pitfalls

### Pitfall 1: Event Loop Block from Embedding
**What goes wrong:** `model.encode(text)` called directly inside `async def` — blocks entire event loop while CPU processes the model.
**Why it happens:** sentence-transformers has no native async API; encode() is synchronous.
**How to avoid:** Always wrap with `await run_in_threadpool(model.encode, text)`.
**Warning signs:** Response times spike to 200-500ms for all concurrent requests during embedding.

### Pitfall 2: Pinecone Index Dimension Locked at Creation
**What goes wrong:** Index created with wrong dimension (e.g., 768) while embedding model produces 384 — all upsert calls fail with dimension mismatch error.
**Why it happens:** `cloud` and `dimension` cannot be changed after index creation.
**How to avoid:** Assert `len(vector) == index_dimension` in EmbeddingClient before first upsert. Log both values at startup.
**Warning signs:** Pinecone upsert returns `Vector dimension X does not match index dimension Y`.

### Pitfall 3: Retrying Non-Retryable Errors
**What goes wrong:** Retry decorator catches all exceptions including 400 (bad request), 401 (auth), 403 (quota exceeded permanently) — wastes time and burns tokens.
**Why it happens:** Using `retry=retry_if_exception_type(Exception)` instead of specific `ResourceExhausted`.
**How to avoid:** Catch only `google.api_core.exceptions.ResourceExhausted` for retry.
**Warning signs:** Tests show retry triggering on validation errors.

### Pitfall 4: Lifespan Partial Initialization
**What goes wrong:** If Pinecone init succeeds but Gemini init fails, app starts in partial state — some requests succeed, some fail silently.
**Why it happens:** Catching `Exception` broadly in lifespan and continuing.
**How to avoid:** Let exceptions propagate — FastAPI will abort startup. Per CONTEXT.md decision: "초기화 실패 시: 전체 서버 시작 중단".
**Warning signs:** Server starts but some endpoints return 500 immediately.

### Pitfall 5: Router AI Confidence Score Expectation
**What goes wrong:** Phase 3 or test code expects `confidence` field in RouterOutput — but router_system_instruction.txt specifies only `mode` and `reason`.
**Why it happens:** Success Criteria in phase description mentions "confidence score" but CONTEXT.md explicitly says no confidence score.
**How to avoid:** RouterOutput Pydantic model has only `mode: int` and `reason: str`. Tests assert these two fields only.
**Warning signs:** JSON parse fails because model doesn't emit confidence field.

### Pitfall 6: PineconeAsyncio Context Manager Leak
**What goes wrong:** Creating `async with PineconeAsyncio()` per request instead of once in lifespan — connection pool exhausted under load.
**Why it happens:** Treating the async context manager as a per-call resource.
**How to avoid:** Initialize once in lifespan, store in app.state, call `close()` in shutdown.
**Warning signs:** `aiohttp.ClientConnectionError` under concurrent load.

## Code Examples

### Lifespan Full Initialization Sequence

```python
# Source: CONTEXT.md decisions + Pinecone official FastAPI guide
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from starlette.concurrency import run_in_threadpool
from pinecone import PineconeAsyncio, ServerlessSpec
from app.clients.pinecone import PineconeClient
from app.clients.embedding import EmbeddingClient
from app.clients.gemini import GeminiClient
from app.clients.router import RouterClient
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # 1. Embedding model (slowest — load first)
    logger.info("Loading embedding model...")
    raw_model = await run_in_threadpool(
        SentenceTransformer, "paraphrase-multilingual-MiniLM-L12-v2"
    )
    app.state.embed_model = EmbeddingClient(raw_model)

    # 2. Pinecone (depends on embedding dimension being known)
    logger.info("Initializing Pinecone...")
    pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
    await pc.__aenter__()
    if not await pc.has_index(settings.PINECONE_INDEX_NAME):
        await pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=384,  # paraphrase-multilingual-MiniLM-L12-v2 output dim
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    desc = await pc.describe_index(settings.PINECONE_INDEX_NAME)
    app.state.pinecone_client = PineconeClient(
        index=pc.IndexAsyncio(host=desc.host)
    )
    app.state._pinecone_control = pc  # keep for shutdown

    # 3. Gemini client
    logger.info("Initializing Gemini client...")
    app.state.gemini_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )

    # 4. Router client
    app.state.router_client = RouterClient(
        api_key=settings.ROUTER_API_KEY,
        model_name=settings.ROUTER_MODEL_NAME,
    )

    logger.info("All clients initialized")
    yield

    # Shutdown
    await app.state.pinecone_client.close()
    await app.state._pinecone_control.__aexit__(None, None, None)
    logger.info("Shutdown complete")
```

### PineconeClient upsert and search

```python
# Source: https://sdk.pinecone.io/python/asyncio.html
from pinecone import Vector
import uuid

class PineconeClient:
    def __init__(self, index) -> None:
        self._index = index

    async def upsert(
        self, user_id: str, vector: list[float], summary: str, timestamp: str
    ) -> None:
        await self._index.upsert(
            vectors=[
                Vector(
                    id=str(uuid.uuid4()),
                    values=vector,
                    metadata={"user_id": user_id, "summary": summary, "timestamp": timestamp},
                )
            ],
            namespace=user_id,
        )

    async def search(self, user_id: str, vector: list[float]) -> list[dict]:
        result = await self._index.query(
            vector=vector,
            top_k=3,
            namespace=user_id,
            include_metadata=True,
        )
        return [m.metadata for m in result.matches]

    async def close(self) -> None:
        await self._index.close()
```

### Mocking Async Clients in Tests

```python
# Source: Python docs unittest.mock + pytest-anyio pattern
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.anyio
async def test_pinecone_search_returns_user_context():
    mock_index = AsyncMock()
    mock_index.query.return_value = AsyncMock(
        matches=[
            AsyncMock(metadata={"summary": "비빔밥 점심", "timestamp": "2026-01-01"})
        ]
    )
    client = PineconeClient(index=mock_index)
    results = await client.search(user_id="user_123", vector=[0.1] * 384)
    assert len(results) == 1
    mock_index.query.assert_awaited_once()

@pytest.mark.anyio
async def test_router_client_classifies_plan_creation():
    mock_genai = AsyncMock()
    mock_genai.aio.models.generate_content.return_value = AsyncMock(
        text='{"mode": 2, "reason": "운동 계획 요청"}'
    )
    client = RouterClient.__new__(RouterClient)
    client._client = mock_genai
    client._model_name = "gemini-2.0-flash-lite"
    result = await client.classify("다음 주 운동 계획 세워줘")
    assert result.mode == 2
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pinecone-client (legacy) | pinecone v8 unified package | 2024 | PineconeAsyncio in same package; no separate grpc install needed |
| google.generativeai SDK | google-genai SDK | 2024 | New SDK has client.aio for native async; response_schema for structured output |
| Manual retry with asyncio.sleep | tenacity with AsyncRetrying | - | Declarative; handles jitter, stop conditions, async transparently |
| response_schema as dict | response_schema as Pydantic class | google-genai 1.x | SDK infers JSON schema from Pydantic model automatically |

**Deprecated/outdated:**
- `google.generativeai` (old SDK): Use `google.genai` (new SDK) — already installed at 1.67.0
- `pinecone-client` package name: Now just `pinecone` on PyPI
- `IndexEmbed` / `create_index_for_model`: For managed embedding indexes — not applicable here since we manage our own embeddings

## Open Questions

1. **Embedding dimension: 384 vs 768**
   - What we know: `paraphrase-multilingual-MiniLM-L12-v2` = 384-dim; `paraphrase-multilingual-mpnet-base-v2` = 768-dim
   - What's unclear: CONTEXT.md says "768-dim 확정" but names MiniLM-L12-v2 — these contradict each other
   - Recommendation: Planner should document the chosen dimension and confirm the model name matches. If Pinecone index already created externally with 768-dim, use mpnet-base-v2. For a fresh index, use MiniLM-L12-v2 at 384-dim (faster, smaller).

2. **Settings env var defaults for GEMINI_MODEL_NAME and ROUTER_MODEL_NAME**
   - What we know: CONTEXT.md says add with default values; ROUTER_MODEL_NAME default = 'gemini-2.0-flash-lite'
   - What's unclear: Default value for GEMINI_MODEL_NAME not specified in CONTEXT.md
   - Recommendation: Use `gemini-2.0-flash` as default for GEMINI_MODEL_NAME; align with project's "Gemini Flash" choice

3. **Pinecone `create_index` wait-for-ready behavior**
   - What we know: Index creation is async; may not be immediately queryable
   - What's unclear: Whether `has_index()` or `describe_index()` blocks until ready
   - Recommendation: Add polling loop or use Pinecone's built-in wait mechanism after create_index; flag for Wave 0 testing

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x + pytest-anyio |
| Config file | none detected — add pytest.ini or pyproject.toml section |
| Quick run command | `pytest tests/test_clients/ -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PINE-01 | PineconeClient.search() and upsert() are awaitable | unit | `pytest tests/test_clients/test_pinecone.py -x` | Wave 0 |
| PINE-02 | upsert/search called with user_id as namespace | unit | `pytest tests/test_clients/test_pinecone.py::test_namespace_isolation -x` | Wave 0 |
| PINE-03 | search returns top_k=3 metadata for correct namespace | unit | `pytest tests/test_clients/test_pinecone.py::test_search_returns_context -x` | Wave 0 |
| PINE-04 | upsert stores vector + metadata with UUID id | unit | `pytest tests/test_clients/test_pinecone.py::test_upsert -x` | Wave 0 |
| EMBD-01 | EmbeddingClient.embed() returns list of floats | unit | `pytest tests/test_clients/test_embedding.py::test_embed_returns_vector -x` | Wave 0 |
| EMBD-02 | embed() calls run_in_threadpool (not blocking) | unit | `pytest tests/test_clients/test_embedding.py::test_embed_uses_threadpool -x` | Wave 0 |
| EMBD-03 | embed() output dimension matches index dimension | unit | `pytest tests/test_clients/test_embedding.py::test_embed_dimension -x` | Wave 0 |
| GEMI-01 | GeminiClient.generate() is awaitable | unit | `pytest tests/test_clients/test_gemini.py -x` | Wave 0 |
| GEMI-02 | generate() retries on ResourceExhausted 3+ times | unit | `pytest tests/test_clients/test_gemini.py::test_retry_on_429 -x` | Wave 0 |
| GEMI-03 | Prompts exist in app/prompts/ as Python constants | unit | `pytest tests/test_prompts.py -x` | Wave 0 |
| GEMI-04 | Mode 7 system prompt references medical_history/allergies/calories | unit | `pytest tests/test_prompts.py::test_meal_prompt_fields -x` | Wave 0 |
| GEMI-05 | Mode 8 system prompt references activity_level/exercise/meal recommendation | unit | `pytest tests/test_prompts.py::test_recommend_prompt_fields -x` | Wave 0 |
| ROUT-01 | RouterClient.classify() returns RouterOutput with mode 1-6 | unit | `pytest tests/test_clients/test_router.py::test_classify_returns_valid_mode -x` | Wave 0 |
| ROUT-02 | RouterClient uses router system prompt constant | unit | `pytest tests/test_clients/test_router.py::test_router_system_prompt -x` | Wave 0 |
| ROUT-03 | RouterClient can be instantiated and called independently | unit | `pytest tests/test_clients/test_router.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_clients/ -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_clients/test_pinecone.py` — covers PINE-01 through PINE-04
- [ ] `tests/test_clients/test_embedding.py` — covers EMBD-01 through EMBD-03
- [ ] `tests/test_clients/test_gemini.py` — covers GEMI-01 through GEMI-02
- [ ] `tests/test_clients/test_router.py` — covers ROUT-01 through ROUT-03
- [ ] `tests/test_prompts.py` — covers GEMI-03 through GEMI-05
- [ ] `tests/test_clients/__init__.py` — package init
- [ ] `tests/conftest.py` — shared fixtures (settings mock, app state mock)
- [ ] Framework install: `pip install "pinecone[asyncio]" sentence-transformers tenacity` — required libs not yet in requirements.txt

## Sources

### Primary (HIGH confidence)
- https://sdk.pinecone.io/python/asyncio.html — PineconeAsyncio, IndexAsyncio, upsert/query namespace API
- https://www.pinecone.io/learn/pinecone-async-fastapi/ — FastAPI lifespan + Pinecone async pattern
- https://googleapis.github.io/python-genai/ — google-genai SDK async client, GenerateContentConfig, response_schema
- https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — confirmed 384-dim output
- https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2 — confirmed 768-dim output
- https://pypi.org/project/tenacity/ — version 9.1.4 (Feb 2026)
- https://pypi.org/project/sentence-transformers/ — version 5.3.0 (Mar 2026)
- google-genai 1.67.0 — verified installed in project environment

### Secondary (MEDIUM confidence)
- https://cloud.google.com/blog/products/ai-machine-learning/learn-how-to-handle-429-resource-exhaustion-errors-in-your-llms — ResourceExhausted exception type for Gemini 429
- https://ai.google.dev/gemini-api/docs/structured-output — response_mime_type + response_json_schema patterns
- FastAPI official docs (starlette.concurrency.run_in_threadpool) — CPU-bound async offload pattern

### Tertiary (LOW confidence)
- None — all critical claims verified through primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via PyPI, SDK installed in project
- Architecture: HIGH — patterns sourced from official Pinecone FastAPI guide and google-genai docs
- Pitfalls: HIGH — dimension mismatch verified against HuggingFace model card; retry exception type from Google Cloud blog

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (30 days — all libraries are stable release versions)
