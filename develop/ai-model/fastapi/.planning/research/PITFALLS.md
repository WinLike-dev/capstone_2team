# Pitfalls Research

**Domain:** FastAPI AI Orchestration Hub — Health/Exercise Domain (RAG + LLM + Vector DB)
**Researched:** 2026-03-21
**Confidence:** HIGH (verified via official docs, leapcell/fastapi official sources, Pinecone docs, Gemini API docs)

---

## Critical Pitfalls

### Pitfall 1: Background Summary Silently Failing Without Detection

**What goes wrong:**
`BackgroundTasks` (또는 `asyncio.create_task`)로 실행하는 Background Summary(요약 → 임베딩 → Pinecone 저장) 파이프라인에서 예외가 발생해도 클라이언트 응답에 전파되지 않는다. Pinecone upsert 실패, LLM 요약 오류, 임베딩 생성 실패 모두 로그에만 남거나 완전히 묻힌다. 결과적으로 벡터 메모리가 조용히 쌓이지 않으면서 "맥락 기반 응답 품질이 향상된다"는 핵심 가치가 무너진다.

**Why it happens:**
FastAPI의 `BackgroundTasks`는 요청 핸들러와 완전히 분리되어 실행된다. 내부에서 exception이 터져도 요청은 이미 200으로 응답 완료 상태이므로 아무도 모른다. 개발 중에는 로컬 환경이 안정적이어서 실패를 경험하지 못한 채 프로덕션에 나간다.

**How to avoid:**
- Background task 함수 전체를 `try/except`로 감싼다.
- 실패 시 structured logging(`logger.error(...)`)으로 반드시 기록한다.
- `asyncio.create_task`를 쓸 경우 `task.add_done_callback()`으로 예외를 캐치한다.
- 가능하면 Background Summary 상태를 추적하는 간단한 in-memory counter(성공/실패 횟수)를 헬스체크 엔드포인트에 노출한다.

```python
async def background_summary(user_id: str, content: str):
    try:
        summary = await summarize(content)
        embedding = await generate_embedding(summary)
        await pinecone_upsert(user_id, embedding, summary)
    except Exception as e:
        logger.error(f"background_summary failed for user={user_id}: {e}")
        # 재시도 전략 또는 dead-letter 큐로 이관
```

**Warning signs:**
- Pinecone 벡터 수가 시간이 지나도 늘어나지 않는다.
- 같은 사용자에 대한 반복 채팅에서 맥락이 전혀 반영되지 않는 응답이 나온다.
- 로그에 background task 관련 출력이 전혀 없다.

**Phase to address:** 프로젝트 기반 설정 단계 (FastAPI 서버 구조 + Background Summary 구현 시)

---

### Pitfall 2: CPU-bound 임베딩 생성이 asyncio 이벤트 루프를 블록

**What goes wrong:**
FastAPI에서 `async def` 엔드포인트 내부에서 sentence-transformers, HuggingFace 모델 등 동기 ML 라이브러리로 임베딩을 생성하면 GIL로 인해 이벤트 루프 전체가 멈춘다. 이 시간 동안 다른 모든 요청이 큐에서 대기한다. Background Summary에서도 동일하게 발생한다.

**Why it happens:**
`async def`로 선언해도 함수 내부에 blocking I/O나 CPU-bound 연산이 있으면 await 없이 실행되는 동안은 이벤트 루프를 점유한다. ML 추론 라이브러리(numpy, torch 등)는 대부분 동기적이다.

**How to avoid:**
- `asyncio.get_event_loop().run_in_executor(None, sync_embed_fn, text)` 또는 `asyncio.to_thread(sync_embed_fn, text)`로 스레드 풀에서 실행한다.
- FastAPI의 `run_in_threadpool`(starlette 내장)을 사용한다.
- 임베딩 모델 로딩은 앱 시작 시 한 번만 수행하고(lifespan 이벤트 활용), 매 요청마다 로딩하지 않는다.

```python
from starlette.concurrency import run_in_threadpool

async def generate_embedding(text: str) -> list[float]:
    return await run_in_threadpool(embedding_model.encode, text)
```

**Warning signs:**
- 동시 요청 시 모든 응답이 순차적으로 도착한다(병렬이 아닌 직렬 처리).
- 단일 요청 응답 시간은 빠른데, 동시 요청 시 P99 레이턴시가 급등한다.
- uvicorn worker가 1개일 때 CPU 사용률이 100%로 고정된다.

**Phase to address:** 임베딩 생성 모듈 구현 단계 (Background Summary + Vector Memory 구축 시)

---

### Pitfall 3: Pinecone에 사용자 격리 없이 벡터 저장

**What goes wrong:**
사용자 구분 없이 단일 namespace에 모든 사용자 벡터를 저장하면, 쿼리 시 다른 사용자의 운동/식단 기억이 검색 결과에 섞인다. 사용자 A의 과거 식단이 사용자 B의 추천에 영향을 준다.

**Why it happens:**
로컬 개발 시 단일 사용자로 테스트하므로 문제가 드러나지 않는다. Pinecone 인덱스에 namespace 파라미터를 명시하지 않으면 기본 namespace(`""`)에 모두 저장된다.

**How to avoid:**
- 모든 upsert와 query에 `namespace=user_id`를 명시한다.
- namespace를 누락한 쿼리는 전체 인덱스를 스캔하므로 검증 레이어에서 namespace 존재를 강제한다.
- 메타데이터에도 `user_id`를 포함시켜 이중 필터링 레이어를 확보한다.

```python
# WRONG — namespace 누락
index.upsert(vectors=[(vec_id, embedding, metadata)])

# CORRECT
index.upsert(vectors=[(vec_id, embedding, metadata)], namespace=str(user_id))

# Query도 반드시 namespace 지정
results = index.query(vector=query_vec, top_k=5, namespace=str(user_id))
```

**Warning signs:**
- 다른 사용자로 로그인했을 때 이전 사용자의 운동 기록이 응답에 언급된다.
- 새 사용자인데 처음부터 과도하게 개인화된 응답이 나온다.
- Pinecone 벡터 수가 예상보다 훨씬 많이 쌓인다.

**Phase to address:** Pinecone 연동 구현 단계

---

### Pitfall 4: Router AI 의도 분류 실패 시 전체 파이프라인 오동작

**What goes wrong:**
Router AI가 잘못된 의도를 분류하면 엉뚱한 Gemini 모드(8가지 중)가 호출된다. 예: 사용자가 "오늘 먹은 거 분석해줘"라고 했는데 채팅 모드가 아닌 추천 모드로 라우팅 → 전혀 다른 정형 데이터 스키마가 반환된다. 의도 분류가 파이프라인의 게이트이므로 분류 오류 = 전체 응답 오류다.

**Why it happens:**
Router AI가 LLM 기반이므로 프롬프트 경계값(애매한 표현, 짧은 문장, 비표준 한국어 표현)에서 불확실한 분류를 한다. 분류 결과에 대한 신뢰도(confidence) 지표 없이 단순 라벨만 반환하도록 설계하면 "50% 확신"과 "99% 확신"이 동일하게 처리된다.

**How to avoid:**
- Router AI 출력에 의도 레이블 + 신뢰도 점수를 함께 반환하도록 프롬프트를 설계한다.
- 신뢰도가 임계값(예: 0.7) 미만일 경우 폴백 처리(기본 채팅 모드 또는 명확화 요청)를 구현한다.
- 각 엔드포인트(`/process-meal`, `/recommend`, `/ai-chat`)는 입력 스키마가 명확히 다르므로, Router AI가 필요한 `/ai-chat` 내부에서만 의도 분류를 수행하고 다른 엔드포인트는 명시적 라우팅으로 처리한다.
- 의도 분류 결과와 실제 사용된 모드를 로그에 기록해 정확도를 모니터링한다.

**Warning signs:**
- 명확한 질문에도 응답 구조(스키마)가 일관성 없이 변한다.
- 식단 분석 요청에 운동 추천 데이터가 섞여 반환된다.
- 사용자 피드백에서 "엉뚱한 답변" 패턴이 반복된다.

**Phase to address:** Router AI 모듈 구현 단계

---

### Pitfall 5: 임베딩 모델 불일치로 Pinecone 검색 품질 붕괴

**What goes wrong:**
저장 시 사용한 임베딩 모델과 쿼리 시 사용한 임베딩 모델이 다르면 코사인 유사도 계산이 완전히 무의미해진다. 예: 저장은 `text-embedding-3-small`(1536차원)으로, 쿼리는 로컬 sentence-transformers(768차원)로 하면 차원 불일치 오류가 발생하거나(Pinecone가 명시적 오류를 던지는 경우), 같은 차원이라도 다른 모델을 쓰면 쓰레기 검색 결과가 나온다.

**Why it happens:**
개발 과정에서 임베딩 모델을 교체할 때 기존 Pinecone 인덱스를 재빌드하지 않는다. 또는 저장 코드와 검색 코드가 분리되어 있어 모델 참조가 일치하지 않게 된다.

**How to avoid:**
- 임베딩 모델은 단일 상수로 중앙 관리한다(`settings.py`에 `EMBEDDING_MODEL_ID`).
- Pinecone 인덱스 메타데이터에 임베딩 모델 ID와 버전을 저장한다.
- 모델 교체 시 인덱스 전체 재빌드 스크립트를 별도로 준비한다.
- upsert 전에 벡터 차원을 검증하는 유틸 레이어를 추가한다.

```python
EMBEDDING_DIM = 768  # 단일 진실 소스

def validate_embedding(vec: list[float]):
    if len(vec) != EMBEDDING_DIM:
        raise ValueError(f"Embedding dim mismatch: expected {EMBEDDING_DIM}, got {len(vec)}")
```

**Warning signs:**
- Pinecone 쿼리가 top_k=5를 요청해도 유사도 점수가 모두 0.1 이하로 나온다.
- 명백히 관련된 과거 기억이 검색되지 않는다.
- 모델 교체 후 갑자기 검색 품질이 저하된다.

**Phase to address:** 임베딩 생성 + Pinecone 연동 구현 단계

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| 단일 Gemini 클라이언트 인스턴스를 전역 변수로 사용 | 빠른 구현 | 멀티스레드 환경에서 race condition, 연결 풀 고갈 | lifespan 이벤트로 초기화하면 OK |
| 모든 Gemini 호출에 재시도 로직 미구현 | 코드 단순화 | 429 에러 시 사용자에게 500 반환, 신뢰성 하락 | Never — 반드시 exponential backoff 구현 |
| Background Summary에서 임베딩 실패 시 무시 | 빠른 응답 보장 | 벡터 메모리 누락 누적, 맥락 품질 저하 | Never — 최소한 로깅과 재시도는 필수 |
| httpx 클라이언트를 요청마다 새로 생성 | 코드 단순화 | 연결 풀 미활용, 레이턴시 증가 | Never — app lifespan에서 shared client 사용 |
| 하드코딩된 Pinecone top_k=10 | 빠른 구현 | 쿼리 비용과 노이즈 불균형 | MVP에서는 허용, 이후 컨텍스트별 튜닝 |
| 프롬프트를 코드 내 문자열로 인라인 작성 | 빠른 구현 | 프롬프트 버전 관리 불가, 실험 어려움 | MVP에서는 허용, 이후 파일/모듈로 분리 |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Pinecone | `query()` 호출 시 `namespace` 파라미터 누락 | 모든 query/upsert에 `namespace=user_id` 강제 |
| Pinecone | 동기 클라이언트를 async 환경에서 사용 | SDK v6.x의 `PineconeAsyncio` 사용 또는 `run_in_threadpool` |
| Gemini Flash | 재시도 없이 직접 호출 | 429 에러에 exponential backoff + jitter 구현 (최소 3회 재시도) |
| Gemini Flash | 모든 토큰 소비를 고려하지 않고 프롬프트 설계 | TPM/RPM/RPD 4가지 차원 모두 모니터링 |
| WAS(Node.js) | FastAPI → WAS 요청에 타임아웃 미설정 | httpx 클라이언트에 `timeout=Timeout(connect=5.0, read=10.0)` 명시 |
| WAS(Node.js) | WAS의 현재 리스트 요청이 실패해도 처리 계속 | 조건부 WAS 요청 실패 시 graceful degradation 전략 정의 |
| httpx | 요청마다 `httpx.AsyncClient()` 새로 생성 | `app.state.http_client`로 lifespan에서 관리하는 shared client 사용 |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| 동기 임베딩 모델을 async 엔드포인트에서 직접 호출 | P99 레이턴시가 P50의 5-10배, 동시 요청 시 직렬 처리 | `run_in_threadpool` 또는 `asyncio.to_thread`로 분리 | 동시 요청 2건 이상 |
| Pinecone top_k 과다 설정 | 검색 비용 증가, 응답에 노이즈 포함 | 엔드포인트별 적절한 top_k 설정 (일반적으로 3-7) | top_k > 20 수준 |
| Background Summary 대기 없이 즉시 쿼리 | 방금 저장한 벡터가 검색 안 됨 | Pinecone 쓰기-읽기 일관성 시간(수 초) 고려, 또는 신규 요청에서는 최신 데이터는 메타데이터 필터로 보완 | 모든 규모 |
| WAS 리스트 요청을 동기 대기 | 채팅 전체 응답 시간 = LLM 시간 + WAS 왕복 시간 | Router AI 의도 분류와 WAS 리스트 요청을 `asyncio.gather`로 병렬 실행 | 첫 번째 채팅 요청부터 |
| Gemini Flash 프롬프트에 불필요한 컨텍스트 포함 | 토큰 소비 증가, TPM 한도 도달 | RAG 검색 결과를 요약 후 프롬프트에 포함, 원문 전체 전달 금지 | TPM 한도 초과 시 |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| 사용자 입력을 그대로 Gemini 프롬프트에 삽입 | Prompt Injection — LLM이 시스템 지시를 무시하고 위험한 건강 조언 생성(FDA 금지 약물, 극단적 식단 등). JAMA 연구에 따르면 94.4% 성공률 | 시스템 프롬프트와 사용자 입력을 명확히 분리, 입력 길이/문자 유형 검증, 출력 스키마 고정(Gemini structured output 활용) |
| Gemini API 키를 코드에 하드코딩 | API 키 유출 시 무제한 API 비용 | 환경변수 또는 `.env` 파일 사용, `.gitignore`에 `.env` 포함 확인 |
| user_id를 클라이언트가 임의로 전달 | 다른 사용자의 벡터 메모리 접근 가능 | WAS가 전달하는 user_id는 JWT 검증 결과에서만 추출, FastAPI가 WAS를 신뢰하는 내부 구조임을 문서화 |
| Pinecone upsert 시 민감 개인 정보를 메타데이터에 저장 | 건강 데이터 유출 시 PIPA/의료정보 보호법 위반 위험 | 메타데이터에는 참조 ID와 타임스탬프만 저장, 원본 식단/운동 텍스트는 필요 최소한으로 요약 후 저장 |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Gemini 응답이 올 때까지 클라이언트에 응답 없음(동기 대기) | LLM 생성 시간(2-8초) 동안 사용자가 멈춘 화면을 봄 | 현재 v1은 REST로 완성 응답 반환이므로, 응답 타임아웃을 합리적으로 설정하고 로딩 상태를 WAS/Front에서 처리하도록 인터페이스 문서화 |
| 8가지 Gemini 모드 스키마가 불일치 | WAS가 응답 파싱에 실패해 Front에 에러 노출 | 모든 모드에 공통 envelope(`mode`, `data`, `error`) 유지, 모드별 `data` 필드만 다르게 설계 |
| 사용자 첫 요청 시 벡터 메모리가 비어 있어 추천이 부정확 | 첫 인상이 나빠 서비스 신뢰도 하락 | Cold start 전략: 첫 요청에서는 메모리 기반 대신 일반적인 건강 기준값(성별/연령 기반)으로 폴백 |
| 건강 도메인 특화 용어를 LLM이 일반 대화로 처리 | "치팅데이" "벌크업" 등 용어 오해석으로 잘못된 칼로리/운동 분석 | 시스템 프롬프트에 도메인 용어집과 컨텍스트를 명시적으로 정의 |

---

## "Looks Done But Isn't" Checklist

- [ ] **Background Summary:** 응답 후 실제로 Pinecone에 벡터가 저장되는지 확인 — Pinecone 콘솔에서 벡터 카운트 증가 검증
- [ ] **Router AI:** 8가지 의도 각각에 대한 분류 정확도 테스트케이스 존재 — 경계값(애매한 질문) 포함 테스트
- [ ] **병렬 처리:** `/ai-chat`에서 Router AI + Vector Search가 실제로 병렬 실행되는지 확인 — `asyncio.gather` 사용 여부 코드 검증
- [ ] **임베딩 일관성:** 저장과 쿼리에 동일한 임베딩 모델 사용 — 단위 테스트에서 동일 텍스트의 저장-검색 round-trip 검증
- [ ] **에러 핸들링:** Gemini API가 429를 반환할 때 클라이언트에 의미 있는 에러 메시지 반환 — 재시도 소진 후 응답 스키마 확인
- [ ] **사용자 격리:** 두 사용자가 동시에 요청했을 때 각자의 벡터만 검색 결과에 나오는지 — 통합 테스트 필수
- [ ] **WAS 연동:** WAS 리스트 요청이 실패했을 때 채팅 응답이 graceful하게 처리되는지 — WAS mock 서버로 타임아웃/500 시나리오 테스트
- [ ] **Gemini 모드 스키마:** 8가지 모드 각각의 응답 스키마가 WAS와 계약(contract)되어 있는지 — 스키마 문서 또는 Pydantic 모델 공유

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Background Summary 누락 누적 | HIGH | 누락 기간 데이터를 WAS에서 재조회 → 배치 요약 → 벡터 재생성 → Pinecone 재업로드 스크립트 작성 |
| Pinecone 임베딩 모델 불일치 | HIGH | 기존 인덱스 전체 삭제 → 새 모델로 전체 재빌드 (다운타임 발생 가능) |
| 사용자 격리 미구현으로 데이터 혼재 | HIGH | 전체 Pinecone 인덱스 삭제 후 메타데이터 기반 재분리 저장 (복구 불가 수준) |
| Router AI 잘못된 분류 패턴 | MEDIUM | 프롬프트 수정 + few-shot 예제 추가 → 재배포 (코드 변경 없음, 빠른 수정 가능) |
| Gemini API 재시도 없어 간헐적 실패 | LOW | 재시도 미들웨어/데코레이터 추가 후 재배포 |
| httpx 타임아웃 미설정으로 연결 hang | MEDIUM | 글로벌 httpx 클라이언트에 타임아웃 추가 → 재배포 |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Background Summary 무음 실패 | Phase: Background Summary 구현 | Background task 내 try/except + 로깅 코드 존재 여부, 실패 시나리오 단위 테스트 |
| CPU-bound 임베딩 이벤트 루프 블록 | Phase: 임베딩 생성 모듈 구현 | `run_in_threadpool` 사용 여부, 동시 요청 10건 부하 테스트 P99 레이턴시 |
| Pinecone 사용자 격리 미구현 | Phase: Pinecone 연동 구현 | 모든 upsert/query에 namespace 파라미터 존재 여부 코드 리뷰 + 통합 테스트 |
| Router AI 분류 실패 전파 | Phase: Router AI + ai-chat 구현 | 신뢰도 점수 출력 확인, 폴백 로직 테스트 |
| 임베딩 모델 불일치 | Phase: 임베딩 생성 모듈 구현 | 저장-검색 round-trip 단위 테스트, 설정 파일 단일 EMBEDDING_MODEL 상수 확인 |
| Gemini 429 재시도 미구현 | Phase: Gemini Flash 연동 구현 | 재시도 데코레이터 존재 여부, mock 429 응답 단위 테스트 |
| httpx 연결 풀 미관리 | Phase: WAS 통신 인터페이스 구현 | lifespan에서 shared httpx.AsyncClient 초기화 코드 존재 여부 |
| 프롬프트 인젝션 | Phase: 각 엔드포인트 구현 | 시스템 프롬프트 분리 구조 확인, 입력 검증 코드 존재 여부 |

---

## Sources

- [Understanding Pitfalls of Async Task Management in FastAPI Requests — Leapcell](https://leapcell.io/blog/understanding-pitfalls-of-async-task-management-in-fastapi-requests) — HIGH confidence
- [Background Tasks — FastAPI Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) — HIGH confidence
- [FastAPI Mistakes That Kill Your Performance — DEV Community](https://dev.to/igorbenav/fastapi-mistakes-that-kill-your-performance-2b8k) — MEDIUM confidence
- [BackgroundTasks blocks entire FastAPI application — GitHub Discussion #11210](https://github.com/fastapi/fastapi/discussions/11210) — HIGH confidence
- [Running Blocking ML Operations — apxml.com/fastapi-ml-deployment](https://apxml.com/courses/fastapi-ml-deployment/chapter-5-async-operations-performance/running-blocking-ml-operations) — MEDIUM confidence
- [Multi-Tenancy in Vector Databases — Pinecone Official](https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/vector-database-multi-tenancy/) — HIGH confidence
- [Implement Multitenancy — Pinecone Docs](https://docs.pinecone.io/guides/index-data/implement-multitenancy) — HIGH confidence
- [Rate Limits — Gemini API Official Docs](https://ai.google.dev/gemini-api/docs/rate-limits) — HIGH confidence
- [Gemini API Error 429 Resource Exhausted Fix Guide](https://www.aifreeapi.com/en/posts/gemini-api-error-429-resource-exhausted-fix) — MEDIUM confidence
- [Building LLM apps with FastAPI — Agents Arcade](https://agentsarcade.com/blog/building-llm-apps-with-fastapi-best-practices) — MEDIUM confidence
- [LLM01:2025 Prompt Injection — OWASP Gen AI Security Project](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — HIGH confidence
- [Vulnerability of LLMs to Prompt Injection in Medical Advice — JAMA Network](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2842987) — HIGH confidence
- [Timeouts — HTTPX Official Docs](https://www.python-httpx.org/advanced/timeouts/) — HIGH confidence
- [FastAPI Async Pitfalls, Performance, Scaling — Mindful Chase](https://www.mindfulchase.com/explore/troubleshooting-tips/back-end-frameworks/troubleshooting-fastapi-async-pitfalls,-performance,-and-scaling-strategies.html) — MEDIUM confidence

---
*Pitfalls research for: FastAPI AI Orchestration Hub (Health/Exercise Domain)*
*Researched: 2026-03-21*
