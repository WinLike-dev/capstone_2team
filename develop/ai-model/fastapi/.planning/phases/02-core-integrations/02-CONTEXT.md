# Phase 2: Core Integrations - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Pinecone, Embedding, Gemini Flash, Router AI — 4개 외부 시스템 클라이언트를 독립적으로 구현하고 테스트 가능하게 만든다. 각 클라이언트는 lifespan에서 초기화되어 app.state에 저장되며, Phase 3에서 엔드포인트가 이 클라이언트들을 조합하여 사용한다. Router AI는 v2(/ai-chat)에서 사용되지만 클라이언트는 이 Phase에서 구현한다.

</domain>

<decisions>
## Implementation Decisions

### 임베딩 모델
- paraphrase-multilingual-MiniLM-L12-v2 (768-dim) 확정
- lifespan 시작 시 1회 로드, app.state.embed_model에 저장
- 임베딩 생성은 run_in_threadpool로 event loop 블록 방지 (EMBD-02)
- Pinecone 인덱스 dimension과 768 일치 보장 (EMBD-03)

### Pinecone 클라이언트
- Serverless 타입, aws/us-east-1 리전
- 코드에서 인덱스 자동 생성 (lifespan에서 인덱스 없으면 create_index)
- namespace 기반 사용자 격리: user_id를 namespace로 사용 (PINE-02)
- 메타데이터 최소한: user_id, summary, timestamp만 저장
- 벡터 ID: UUID4 생성
- 검색 top_k: 3
- 테스트: 모킹만 (실제 Pinecone 연결 없음)
- 테스트용 별도 인덱스 불필요

### Gemini Flash 클라이언트
- google-genai SDK 사용 (GEMI-01)
- 모델명: 환경변수 GEMINI_MODEL_NAME으로 Settings에 추가 (기본값 설정)
- JSON 출력 강제: response_mime_type='application/json' + response_schema (SDK 레벨 보장)
- 모드별 프롬프트: app/prompts/ 디렉토리에 Python 상수로 관리 (GEMI-03)
- 프롬프트 템플릿: f-string/.format()으로 user_profile 필드를 시스템 프롬프트에 주입 (GEMI-04, GEMI-05)
- 한국어 응답: 시스템 프롬프트에 '한국어로 응답하세요' 명시
- 재시도: tenacity 라이브러리로 exponential backoff + jitter (GEMI-02)
- 테스트: 모킹만 (실제 API 호출 없음)

### Router AI 클라이언트
- Gemini Flash Lite 사용 (별도 경량 모델)
- 별도 API 키: ROUTER_API_KEY 환경변수를 Settings에 추가
- 모델명: ROUTER_MODEL_NAME 환경변수 (기본값 'gemini-2.0-flash-lite')
- 별도 클라이언트: clients/router.py에 RouterClient 분리 (ROUT-03 단독 테스트)
- 출력 형식: mode + reason만 (router_system_instruction.txt 기준, confidence score 없음)
- 시스템 프롬프트: docs/router_system_instruction.txt 내용을 app/prompts/router.py로 Python 상수로 이전
- Phase 2 범위: 클라이언트 + 단독 테스트만. 엔드포인트 연동은 v2

### 클라이언트 초기화/생명주기
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

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/core/config.py`: Settings 클래스 — GEMINI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME, WAS_BASE_URL 이미 정의. GEMINI_MODEL_NAME, ROUTER_API_KEY, ROUTER_MODEL_NAME 추가 필요
- `app/core/lifespan.py`: lifespan placeholder — 클라이언트 초기화 코드 추가 위치 확보됨
- `app/schemas/common.py`: ErrorDetail, SuccessResponse, ErrorResponse — 에러 envelope 포맷 확립
- `app/schemas/meal.py`, `app/schemas/recommend.py`: Gemini 응답 파싱에 활용할 Pydantic 모델 존재

### Established Patterns
- pydantic-settings: 환경변수 관리 패턴 확립 (lru_cache 싱글턴)
- 4계층 구조: routers/services/clients/core — 클라이언트는 app/clients/ 에 배치
- 에러 응답: {status: "error", error: {code, message}} envelope

### Integration Points
- `app/clients/__init__.py`: 빈 상태 — Pinecone, Embedding, Gemini, Router 클라이언트 추가
- `app/core/lifespan.py`: startup에서 클라이언트 초기화, shutdown에서 정리
- `app/services/__init__.py`: 빈 상태 — Phase 3에서 서비스 레이어가 클라이언트 조합

</code_context>

<specifics>
## Specific Ideas

- Gemini Mode 7(식단 분석): 사용자 프로필(medical_history, allergies)과 식단 메시지를 받아 칼로리 분석 + 간결한 피드백 메시지 반환
- Gemini Mode 8(추천): 사용자 프로필(activity_level)과 지시사항을 받아 운동/식단 추천 반환
- Router AI 시스템 지침서: docs/router_system_instruction.txt 참조 — 6가지 모드(단순대화/플랜작성/플랜수정/식단작성/식단수정/DB수정), JSON 출력({mode, reason})
- 추가할 환경변수: GEMINI_MODEL_NAME, ROUTER_API_KEY, ROUTER_MODEL_NAME
- 추가할 의존성: sentence-transformers, pinecone, google-genai, tenacity

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-core-integrations*
*Context gathered: 2026-03-22*
