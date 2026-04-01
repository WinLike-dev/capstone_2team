# Phase 3: Endpoints and Memory - Research

**Researched:** 2026-03-22
**Domain:** FastAPI service layer, BackgroundTasks, graceful degradation, global exception handling
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- 엔드포인트당 서비스 함수 1개: meal_service.process_meal(), recommend_service.recommend()
- 각 함수가 전체 파이프라인 오케스트레이션 (Pinecone 검색 → Gemini 호출 → Background Summary 등록)
- 파일 구조: app/services/meal_service.py, app/services/recommend_service.py, app/services/background_summary.py (공용)
- 클라이언트 접근: request.app.state에서 직접 (app.state.gemini_client 등)
- BackgroundTasks는 서비스 함수가 인자로 받아 직접 add_task()
- Background Summary 요약 내용: 사용자 메시지 + AI 응답 둘 다 포함
- 별도 요약 프롬프트: app/prompts/summary.py에 전용 프롬프트
- 실패 시: 재시도 없음, 로그만 남기고 무시. 메인 응답에 영향 없음 (BGSM-05)
- 메타데이터: 기존 3개만 유지 (user_id, summary, timestamp)
- 검색 쿼리: 사용자 메시지(user_message 또는 user_instruction)를 그대로 임베딩
- 주입 형식: 번호 매기기 ('이전 맥락:\n1. [summary1]\n2. [summary2]\n3. [summary3]')
- 주입 위치: 시스템 프롬프트 내 '이전 맥락:' 섹션으로 포함
- 검색 결과 없을 때(첫 요청): '이전 맥락: 없음'으로 표시하고 Gemini 호출 진행
- top_k=3 유지
- Gemini 실패: 500 + ErrorResponse(code='GEMINI_ERROR')
- Pinecone 검색 실패: 경고 로그 남기고 맥락 없이 계속 진행
- 요청 검증 실패: 422 (FastAPI/Pydantic 기본 동작)
- 예상치 못한 에러: 글로벌 exception_handler로 Exception catch → 500 + ErrorResponse(code='INTERNAL_ERROR') + 스택트레이스 로그

### Claude's Discretion
- 서비스 함수 내부 세부 구조 (헬퍼 함수 분리 여부)
- Background Summary용 Gemini 호출 시 response_schema 사용 여부
- 글로벌 예외 핸들러의 정확한 구현 방식 (미들웨어 vs exception_handler 데코레이터)
- 프롬프트에 맥락 주입 시 정확한 포매팅 (Phase 2 프롬프트 빌더와 통합 방식)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MEAL-01 | POST /process-meal 엔드포인트 구현 | 기존 stub router를 서비스 호출로 교체. FastAPI Request 객체로 app.state 접근 |
| MEAL-02 | 요청 처리: user_id, user_profile, user_instruction, user_message 수신 | 기존 ProcessMealRequest 스키마 그대로 사용 |
| MEAL-03 | Pinecone 벡터 검색 (사용자 맥락 조회) | PineconeClient.search() 래퍼 확인 완료. 실패 시 graceful degradation 패턴 필요 |
| MEAL-04 | Gemini Flash 호출 (식단 분석 → 칼로리 + 메시지 반환) | GeminiClient.generate() + build_meal_system_prompt() 확장 (맥락 주입) |
| MEAL-05 | 응답 형식: {status, data: {calories, message}} | SuccessResponse + MealAnalysisData 스키마 이미 완성 |
| RECOM-01 | POST /recommend 엔드포인트 구현 | 기존 stub router를 서비스 호출로 교체 |
| RECOM-02 | 요청 처리: user_id, user_profile, user_instruction 수신 | 기존 RecommendRequest 스키마 그대로 사용 |
| RECOM-03 | Pinecone 벡터 검색 (사용자 맥락 조회) | MEAL-03과 동일 패턴 |
| RECOM-04 | Gemini Flash 호출 (운동/식단 추천 생성) | GeminiClient.generate() + build_recommend_system_prompt() 확장 |
| RECOM-05 | 응답 형식: {status, data: {recommended_exercise: ..., recommended_meal: ...}} | SuccessResponse + RecommendationData 스키마 이미 완성 |
| BGSM-01 | BackgroundTasks 기반 비동기 메모리 파이프라인 구현 | FastAPI BackgroundTasks.add_task() — 응답 반환 후 실행 보장 |
| BGSM-02 | Gemini Flash로 질문+답변 요약 생성 | 전용 summary.py 프롬프트 + GeminiClient.generate() 호출 |
| BGSM-03 | 요약 텍스트 임베딩 생성 | EmbeddingClient.embed() 사용 (384-dim) |
| BGSM-04 | Pinecone에 벡터 임베딩 + user_id + 요약 + timestamp 저장 | PineconeClient.upsert() — timestamp는 내부에서 자동 생성 |
| BGSM-05 | 에러 발생 시 로깅 (무음 실패 방지) | try/except + logger.exception() 패턴. 메인 응답에 영향 없음 |
</phase_requirements>

---

## Summary

Phase 3는 Phase 1에서 만든 stub 엔드포인트 2개를 실제 파이프라인으로 교체하고, 응답 후 비동기로 대화 요약을 Pinecone에 저장하는 Background Summary 파이프라인을 추가한다. 모든 인프라(GeminiClient, PineconeClient, EmbeddingClient)가 Phase 2에서 완성되었으므로, Phase 3는 이들을 서비스 레이어에서 조합(orchestrate)하는 것이 핵심 작업이다.

가장 중요한 설계 패턴은 두 가지다: (1) Pinecone 검색 실패 시 에러를 삼키고 맥락 없이 계속 진행하는 graceful degradation, (2) 응답 반환 후 Background Summary가 실행되도록 FastAPI BackgroundTasks를 서비스 레이어에서 add_task()로 등록하는 패턴. 글로벌 예외 핸들러는 main.py에 @app.exception_handler(Exception) 데코레이터로 등록하여 모든 미처리 에러를 일관된 ErrorResponse 포맷으로 변환한다.

**Primary recommendation:** 서비스 함수는 "Pinecone 검색(graceful) → 프롬프트 빌드 → Gemini 호출 → 응답 직렬화 → BackgroundTasks 등록" 순서로 구성하고, 모든 클라이언트는 `request.app.state`에서 꺼낸다.

## Standard Stack

### Core (이미 requirements.txt에 포함)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | >=0.115.0 | BackgroundTasks, exception_handler, Request | 이미 프로젝트 코어 |
| pydantic | >=2.0 | 응답 스키마 직렬화, response_schema | 이미 확립된 패턴 |
| google-genai | >=1.0 | Gemini Flash API (GeminiClient 래핑) | 이미 확립된 패턴 |
| pinecone[asyncio] | >=8.0 | 벡터 upsert/search (PineconeClient 래핑) | 이미 확립된 패턴 |
| sentence-transformers | >=5.0 | 텍스트 임베딩 (EmbeddingClient 래핑) | 이미 확립된 패턴 |

### New Files (Phase 3 신규 추가)
| File | Purpose |
|------|---------|
| app/services/meal_service.py | process_meal() 파이프라인 오케스트레이터 |
| app/services/recommend_service.py | recommend() 파이프라인 오케스트레이터 |
| app/services/background_summary.py | run_background_summary() 비동기 파이프라인 |
| app/prompts/summary.py | 요약 전용 Gemini 프롬프트 |

**New packages needed:** 없음 — 기존 requirements.txt 완전 충족.

## Architecture Patterns

### Recommended Project Structure (Phase 3 추가분)
```
app/
├── services/
│   ├── __init__.py          # 현재 비어있음 — 재수출 추가
│   ├── meal_service.py      # (신규) process_meal() 오케스트레이터
│   ├── recommend_service.py # (신규) recommend() 오케스트레이터
│   └── background_summary.py # (신규) 비동기 메모리 파이프라인
├── prompts/
│   └── summary.py           # (신규) 요약 전용 프롬프트
├── routers/
│   ├── meal.py              # stub body → service 호출로 교체
│   └── recommend.py         # stub body → service 호출로 교체
└── main.py                  # 글로벌 예외 핸들러 추가
```

### Pattern 1: 라우터에서 서비스 호출 (Request 객체 전달)

**What:** 라우터 함수는 얇게 유지하고, Request와 BackgroundTasks를 서비스 함수에 위임.
**When to use:** 모든 엔드포인트 핸들러.

```python
# app/routers/meal.py (Phase 3 교체 후)
from fastapi import APIRouter, BackgroundTasks, Request
from app.schemas.common import SuccessResponse
from app.schemas.meal import ProcessMealRequest
from app.services.meal_service import process_meal

router = APIRouter(tags=["meal"])

@router.post("/process-meal", response_model=SuccessResponse)
async def process_meal_endpoint(
    body: ProcessMealRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    return await process_meal(body, request, background_tasks)
```

### Pattern 2: 서비스 함수 파이프라인 오케스트레이션

**What:** 서비스 함수가 전체 파이프라인을 순서대로 실행.
**Pipeline order:** Pinecone 검색(graceful) → 프롬프트 빌드 → Gemini 호출 → 응답 직렬화 → BackgroundTasks 등록.

```python
# app/services/meal_service.py (핵심 구조)
import logging
from fastapi import BackgroundTasks, Request
from app.schemas.meal import ProcessMealRequest, MealAnalysisData
from app.schemas.common import SuccessResponse
from app.prompts.meal import build_meal_system_prompt
from app.services.background_summary import run_background_summary

logger = logging.getLogger(__name__)

async def process_meal(
    body: ProcessMealRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client

    # 1. Pinecone 맥락 검색 (실패해도 계속)
    context_text = await _fetch_context(pinecone, embed, body.user_id, body.user_message)

    # 2. 시스템 프롬프트 빌드 (맥락 주입)
    system_prompt = build_meal_system_prompt(body.user_profile, context_text)

    # 3. Gemini 호출
    raw_json = await gemini.generate(
        system_prompt=system_prompt,
        user_content=body.user_message,
        response_schema=MealAnalysisData,
    )

    # 4. 응답 파싱
    import json
    data = MealAnalysisData(**json.loads(raw_json))

    # 5. Background Summary 등록 (응답 반환 후 실행)
    background_tasks.add_task(
        run_background_summary,
        user_id=body.user_id,
        user_message=body.user_message,
        ai_response=data.message,
        gemini_client=gemini,
        embed_client=embed,
        pinecone_client=pinecone,
    )

    return SuccessResponse(data=data.model_dump())
```

### Pattern 3: Graceful Degradation (Pinecone 검색 실패)

**What:** 검색 실패 시 경고 로그 후 빈 맥락으로 계속 진행.
**Why critical:** Pinecone 장애가 전체 요청을 블록하면 안 됨.

```python
async def _fetch_context(pinecone, embed, user_id: str, query: str) -> str:
    """맥락 검색 실패 시 '이전 맥락: 없음' 반환."""
    try:
        vector = await embed.embed(query)
        results = await pinecone.search(user_id=user_id, vector=vector, top_k=3)
        if not results:
            return "이전 맥락: 없음"
        lines = "\n".join(
            f"{i+1}. {r['summary']}" for i, r in enumerate(results)
        )
        return f"이전 맥락:\n{lines}"
    except Exception:
        logger.warning("Pinecone context fetch failed for user=%s, continuing without context", user_id)
        return "이전 맥락: 없음"
```

### Pattern 4: 프롬프트 빌더 맥락 주입 확장

**What:** 기존 build_meal_system_prompt(), build_recommend_system_prompt()에 context_text 파라미터 추가.
**Why:** CONTEXT.md 결정: 시스템 프롬프트 내 '이전 맥락:' 섹션으로 주입.

```python
# app/prompts/meal.py 확장 (시그니처 변경)
def build_meal_system_prompt(user_profile: UserProfile, context_text: str = "이전 맥락: 없음") -> str:
    ...
    return (
        "당신은 식단 분석 전문가입니다.\n"
        f"사용자 프로필: 성별={gender}, 나이={age}, ...\n"
        f"{context_text}\n"          # ← 맥락 주입
        "사용자가 제공하는 식단 정보를 분석하여...\n"
        "한국어로 응답하세요."
    )
```

### Pattern 5: Background Summary 파이프라인

**What:** 응답 후 비동기 실행. try/except로 완전 격리 — 실패해도 아무 것도 re-raise 안 함.

```python
# app/services/background_summary.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def run_background_summary(
    user_id: str,
    user_message: str,
    ai_response: str,
    gemini_client,
    embed_client,
    pinecone_client,
) -> None:
    """응답 후 비동기로 실행. 실패 시 로그만 남기고 종료."""
    try:
        from app.prompts.summary import build_summary_prompt, SummaryOutput
        prompt = build_summary_prompt()
        content = f"질문: {user_message}\n답변: {ai_response}"
        raw = await gemini_client.generate(
            system_prompt=prompt,
            user_content=content,
            response_schema=SummaryOutput,
        )
        import json
        summary_text = json.loads(raw)["summary"]

        vector = await embed_client.embed(summary_text)
        await pinecone_client.upsert(
            user_id=user_id,
            vector=vector,
            summary=summary_text,
        )
    except Exception:
        logger.exception("Background summary failed for user=%s", user_id)
```

### Pattern 6: 글로벌 예외 핸들러

**What:** @app.exception_handler(Exception) 데코레이터로 모든 미처리 예외를 ErrorResponse 포맷으로 변환.
**Decision note (Claude's Discretion):** exception_handler 데코레이터 방식 권장. 미들웨어보다 단순하고 FastAPI의 표준 패턴.

```python
# app/main.py 추가
import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception: %s\n%s",
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {"code": "INTERNAL_ERROR", "message": "내부 서버 오류가 발생했습니다."},
        },
    )
```

**주의:** Gemini 실패(code='GEMINI_ERROR')는 서비스 레이어에서 명시적으로 HTTPException(500)을 raise하거나, 글로벌 핸들러에서 genai_errors.ClientError를 별도로 catch하는 두 가지 방법이 가능하다. 서비스 레이어에서 명시적으로 raise HTTPException이 더 명확하다.

### Pattern 7: Summary 프롬프트 (app/prompts/summary.py)

**What:** 요약 전용 프롬프트 + Pydantic 스키마 (response_schema용).
**Decision (Claude's Discretion):** Background Summary용 Gemini 호출도 response_schema 사용 권장 — JSON 파싱 안정성을 위해.

```python
# app/prompts/summary.py
from pydantic import BaseModel

class SummaryOutput(BaseModel):
    summary: str

SUMMARY_SYSTEM_PROMPT: str = (
    "당신은 대화 요약 전문가입니다.\n"
    "주어진 질문과 답변을 2-3문장으로 간결하게 요약하세요.\n"
    "한국어로 응답하세요."
)

def build_summary_prompt() -> str:
    return SUMMARY_SYSTEM_PROMPT
```

### Anti-Patterns to Avoid

- **서비스에서 app.state 직접 import:** `from app.main import app` 후 `app.state` 접근은 순환 import를 유발. 항상 `request.app.state`를 사용.
- **BackgroundTasks를 라우터에서만 사용:** 서비스 테스트 시 BackgroundTasks mock을 주입할 수 없게 됨. 서비스 함수가 인자로 받아야 함 (결정 사항 준수).
- **Background Summary 실패 re-raise:** run_background_summary에서 예외를 상위로 전파하면 FastAPI가 에러 응답을 보낸다. 반드시 try/except로 완전 격리.
- **Pinecone 검색 실패를 500으로 처리:** 결정 사항: 경고 로그 후 맥락 없이 계속. 검색 실패 != 서비스 실패.
- **글로벌 핸들러가 HTTPException을 가로채기:** FastAPI는 HTTPException을 별도로 처리. `Exception` 핸들러는 HTTPException을 catch하지 않도록 주의 (FastAPI 기본 동작상 HTTPException이 먼저 처리됨, 별도 핸들러 등록 불필요).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 응답 후 비동기 작업 | 별도 asyncio.create_task() 관리 | FastAPI BackgroundTasks | 라이프사이클 관리, 테스트 용이성 |
| JSON 스키마 강제 | 수동 JSON 파싱 + 검증 | response_schema (google-genai SDK) | SDK 레벨에서 타입 강제 |
| 에러 응답 포맷 | 각 라우터에서 JSONResponse 직접 생성 | 글로벌 exception_handler | 일관성, 중복 제거 |
| 임베딩 생성 | 직접 SentenceTransformer.encode() | EmbeddingClient.embed() | threadpool 래핑, 테스트 mock 용이 |
| 벡터 저장/검색 | 직접 index.upsert() / index.query() | PineconeClient.upsert() / search() | namespace 격리, UUID 생성, timestamp 자동화 |

**Key insight:** 모든 인프라 복잡성(retry, threadpool, namespace 격리, JSON 강제)은 Phase 2에서 클라이언트 레이어에 캡슐화되었다. Phase 3는 오케스트레이션만 담당한다.

## Common Pitfalls

### Pitfall 1: FastAPI BackgroundTasks와 app.state 접근

**What goes wrong:** Background task 함수 내에서 `request.app.state`를 참조할 수 없음 — request 객체가 없음.
**Why it happens:** BackgroundTasks는 응답 반환 후 별도로 실행되므로 request context가 없다.
**How to avoid:** 서비스 함수에서 클라이언트 인스턴스를 꺼낸 후, 클라이언트 객체 자체를 background task 함수의 인자로 전달. (위 Pattern 5 코드 참조)
**Warning signs:** background task 함수 시그니처에 `request: Request`가 있으면 잘못된 것.

### Pitfall 2: 글로벌 예외 핸들러가 422 응답을 덮어씀

**What goes wrong:** `@app.exception_handler(Exception)`이 RequestValidationError(422)를 가로채서 500으로 응답.
**Why it happens:** RequestValidationError는 Exception의 서브클래스.
**How to avoid:** RequestValidationError는 FastAPI가 별도로 처리하므로 일반적으로 문제없으나, 확실하게 하려면 핸들러에서 `from fastapi.exceptions import RequestValidationError`를 체크하거나 Exception 대신 더 구체적인 타입만 catch.
**실제로:** FastAPI는 RequestValidationError를 내부적으로 먼저 처리하므로 `@app.exception_handler(Exception)` 등록만으로는 422가 500으로 바뀌지 않는다. 하지만 안전을 위해 테스트로 확인 필요.

### Pitfall 3: Gemini response_schema에 Optional 필드 혼입

**What goes wrong:** response_schema Pydantic 모델에 Optional 필드가 있으면 Gemini가 간헐적으로 null을 포함한 JSON을 반환해 파싱 실패.
**Why it happens:** Gemini JSON 강제는 스키마 그대로 따르는데, Optional이 있으면 null 허용.
**How to avoid:** SummaryOutput과 같은 summary 스키마는 모든 필드를 required(non-Optional)로 정의.

### Pitfall 4: Background Summary용 Gemini 호출이 메인 응답을 지연

**What goes wrong:** Background task를 `add_task()` 전에 await하면 응답이 지연됨.
**Why it happens:** 순서 실수 — `await run_background_summary(...)` vs `background_tasks.add_task(run_background_summary, ...)`.
**How to avoid:** 반드시 `background_tasks.add_task(fn, **kwargs)` 패턴 사용. await 하지 않음.

### Pitfall 5: 프롬프트 빌더 시그니처 변경 시 기존 테스트 파괴

**What goes wrong:** build_meal_system_prompt()와 build_recommend_system_prompt()에 context_text 파라미터 추가 시, 기존 Phase 2 테스트가 positional arg 불일치로 실패.
**Why it happens:** 기존 테스트가 2인수 호출 (user_profile만)을 사용.
**How to avoid:** context_text 파라미터에 기본값 제공: `context_text: str = "이전 맥락: 없음"`. 기존 테스트 변경 불필요.

## Code Examples

### 서비스 레이어에서 GeminiClient 에러를 HTTPException으로 변환

```python
# app/services/meal_service.py
from fastapi import HTTPException
from google.genai import errors as genai_errors
from app.schemas.common import ErrorDetail, ErrorResponse

async def process_meal(body, request, background_tasks) -> SuccessResponse:
    ...
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=body.user_message,
            response_schema=MealAnalysisData,
        )
    except genai_errors.ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error": {"code": "GEMINI_ERROR", "message": str(exc)}},
        )
    ...
```

### BackgroundTasks.add_task() 호출 (응답 전 등록, 응답 후 실행)

```python
# 서비스 함수 마지막 단계
background_tasks.add_task(
    run_background_summary,
    user_id=body.user_id,
    user_message=body.user_message,
    ai_response=result_message,
    gemini_client=gemini,
    embed_client=embed,
    pinecone_client=pinecone,
)
return SuccessResponse(data=data.model_dump())
# FastAPI가 응답을 보낸 후 run_background_summary()를 실행함
```

### 맥락 포매팅 (결정 사항 그대로)

```python
# top_k=3 결과를 번호 매기기 포맷으로
def _format_context(results: list[dict]) -> str:
    if not results:
        return "이전 맥락: 없음"
    lines = "\n".join(f"{i+1}. {r['summary']}" for i, r in enumerate(results))
    return f"이전 맥락:\n{lines}"
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| asyncio.create_task() for fire-and-forget | FastAPI BackgroundTasks.add_task() | 테스트 용이성, 라이프사이클 관리 |
| 수동 JSON 파싱 | google-genai response_schema | 타입 안전, 파싱 에러 최소화 |
| 미들웨어로 글로벌 에러 처리 | @app.exception_handler(Exception) 데코레이터 | 단순성, FastAPI 표준 패턴 |

## Open Questions

1. **GeminiClient.generate()의 response_schema가 Pydantic v2 모델을 그대로 수락하는지 확인 필요**
   - What we know: Phase 2에서 `response_mime_type=application/json + response_schema=Pydantic모델`로 작동 확인됨
   - What's unclear: SummaryOutput 같은 단순 1-field 스키마에서도 동일하게 작동하는지
   - Recommendation: Wave 0에서 SummaryOutput 스키마로 단위 테스트 작성 후 확인

2. **글로벌 exception_handler가 HTTPException을 가로채는지 환경 검증**
   - What we know: FastAPI 내부에서 HTTPException을 먼저 처리함
   - What's unclear: 특정 FastAPI 버전(>=0.115.0)에서 동작이 다를 수 있음
   - Recommendation: 통합 테스트에서 422 응답이 500으로 바뀌지 않는지 검증 케이스 추가

## Validation Architecture

> nyquist_validation: true (config.json)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-anyio (기존 설치됨) |
| Config file | conftest.py (루트) |
| Quick run command | `pytest tests/test_meal_service.py tests/test_recommend_service.py tests/test_background_summary.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MEAL-01 | POST /process-meal 200 응답 (실제 서비스 호출) | integration | `pytest tests/test_endpoints.py::test_process_meal_calls_service -x` | ❌ Wave 0 |
| MEAL-02 | 요청 필드 수신 및 서비스에 전달 | unit | `pytest tests/test_meal_service.py::test_process_meal_passes_fields -x` | ❌ Wave 0 |
| MEAL-03 | Pinecone 검색 실패 시 graceful degradation | unit | `pytest tests/test_meal_service.py::test_process_meal_pinecone_failure -x` | ❌ Wave 0 |
| MEAL-04 | Gemini 호출 및 응답 파싱 | unit | `pytest tests/test_meal_service.py::test_process_meal_gemini_call -x` | ❌ Wave 0 |
| MEAL-05 | 응답 형식 {status, data: {calories, message}} | unit | `pytest tests/test_meal_service.py::test_process_meal_response_format -x` | ❌ Wave 0 |
| RECOM-01 | POST /recommend 200 응답 (실제 서비스 호출) | integration | `pytest tests/test_endpoints.py::test_recommend_calls_service -x` | ❌ Wave 0 |
| RECOM-02 | 요청 필드 수신 및 서비스에 전달 | unit | `pytest tests/test_recommend_service.py::test_recommend_passes_fields -x` | ❌ Wave 0 |
| RECOM-03 | Pinecone 검색 실패 시 graceful degradation | unit | `pytest tests/test_recommend_service.py::test_recommend_pinecone_failure -x` | ❌ Wave 0 |
| RECOM-04 | Gemini 호출 및 응답 파싱 | unit | `pytest tests/test_recommend_service.py::test_recommend_gemini_call -x` | ❌ Wave 0 |
| RECOM-05 | 응답 형식 {status, data: {recommended_exercise, recommended_meal}} | unit | `pytest tests/test_recommend_service.py::test_recommend_response_format -x` | ❌ Wave 0 |
| BGSM-01 | BackgroundTasks.add_task()로 등록됨 | unit | `pytest tests/test_meal_service.py::test_background_task_registered -x` | ❌ Wave 0 |
| BGSM-02 | Gemini로 요약 생성 | unit | `pytest tests/test_background_summary.py::test_summary_gemini_call -x` | ❌ Wave 0 |
| BGSM-03 | 요약 텍스트 임베딩 생성 | unit | `pytest tests/test_background_summary.py::test_summary_embed_call -x` | ❌ Wave 0 |
| BGSM-04 | Pinecone upsert 호출 | unit | `pytest tests/test_background_summary.py::test_summary_pinecone_upsert -x` | ❌ Wave 0 |
| BGSM-05 | 에러 발생 시 로그 기록, 예외 전파 안 함 | unit | `pytest tests/test_background_summary.py::test_summary_error_silent -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_meal_service.py tests/test_recommend_service.py tests/test_background_summary.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_meal_service.py` — covers MEAL-01 through MEAL-05, BGSM-01
- [ ] `tests/test_recommend_service.py` — covers RECOM-01 through RECOM-05
- [ ] `tests/test_background_summary.py` — covers BGSM-02 through BGSM-05
- [ ] `tests/test_endpoints.py` — integration tests (서비스 mock 후 엔드포인트 호출)
- [ ] `app/prompts/summary.py` — Wave 0에서 파일 생성 필요 (테스트 임포트 경로)

## Sources

### Primary (HIGH confidence)
- 기존 코드베이스 직접 분석:
  - `app/clients/gemini.py` — GeminiClient.generate() 시그니처, tenacity 패턴
  - `app/clients/pinecone.py` — PineconeClient.upsert(), search() 시그니처
  - `app/clients/embedding.py` — EmbeddingClient.embed() 시그니처
  - `app/prompts/meal.py`, `app/prompts/recommend.py` — 프롬프트 빌더 구조
  - `app/routers/meal.py`, `app/routers/recommend.py` — stub 구조 확인
  - `app/main.py` — 현재 main.py 구조
  - `app/core/lifespan.py` — app.state 클라이언트 저장 패턴
  - `tests/test_lifespan.py` — mock 패턴 (Phase 3 테스트 참조용)
  - `.planning/phases/03-endpoints-and-memory/03-CONTEXT.md` — 모든 결정 사항
- FastAPI 공식 문서 (훈련 지식): BackgroundTasks, Request, exception_handler 패턴

### Secondary (MEDIUM confidence)
- FastAPI BackgroundTasks 동작: 응답 반환 후 실행 보장 — 공식 문서 기반 훈련 지식

### Tertiary (LOW confidence)
- 없음

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 모든 라이브러리가 이미 requirements.txt에 존재하며 Phase 2에서 작동 확인됨
- Architecture: HIGH — 기존 코드베이스 직접 분석으로 모든 클라이언트 시그니처 확인 완료
- Pitfalls: MEDIUM — FastAPI BackgroundTasks + app.state 조합의 edge case는 훈련 지식 기반

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (안정적 라이브러리, 30일)
