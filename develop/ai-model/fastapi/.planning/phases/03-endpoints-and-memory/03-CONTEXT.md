# Phase 3: Endpoints and Memory - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

WAS가 POST /process-meal과 POST /recommend를 호출하면 AI 분석 결과를 반환하고, 응답 후 대화 맥락(질문+답변 요약)이 Pinecone에 비동기로 저장된다. Phase 1의 stub 엔드포인트를 실제 서비스 로직으로 교체하고, Phase 2의 클라이언트들을 서비스 레이어에서 조합한다.

</domain>

<decisions>
## Implementation Decisions

### 서비스 레이어 구조
- 엔드포인트당 서비스 함수 1개: meal_service.process_meal(), recommend_service.recommend()
- 각 함수가 전체 파이프라인 오케스트레이션 (Pinecone 검색 → Gemini 호출 → Background Summary 등록)
- 파일 구조: app/services/meal_service.py, app/services/recommend_service.py, app/services/background_summary.py (공용)
- 클라이언트 접근: request.app.state에서 직접 (app.state.gemini_client 등)
- BackgroundTasks는 서비스 함수가 인자로 받아 직접 add_task()

### Background Summary 파이프라인
- 요약 내용: 사용자 메시지 + AI 응답 둘 다 포함
- 별도 요약 프롬프트: app/prompts/summary.py에 전용 프롬프트 ('질문과 답변을 2-3문장으로 요약하세요' 형태)
- 실패 시: 재시도 없음, 로그만 남기고 무시. 메인 응답에 영향 없음 (BGSM-05)
- 메타데이터: 기존 3개만 유지 (user_id, summary, timestamp) — Phase 2 결정 그대로

### 맥락 검색 주입 방식
- 검색 쿼리: 사용자 메시지(user_message 또는 user_instruction)를 그대로 임베딩
- 주입 형식: 번호 매기기 ('이전 맥락:\n1. [summary1]\n2. [summary2]\n3. [summary3]')
- 주입 위치: 시스템 프롬프트 내 '이전 맥락:' 섹션으로 포함
- 검색 결과 없을 때(첫 요청): '이전 맥락: 없음'으로 표시하고 Gemini 호출 진행
- top_k=3 유지 (Phase 2 결정)

### 에러 처리 전략
- Gemini 실패: 500 + ErrorResponse(code='GEMINI_ERROR') — tenacity retry 후에도 실패한 경우
- Pinecone 검색 실패: 경고 로그 남기고 맥락 없이 계속 진행. 사용자는 정상 응답 받음
- 요청 검증 실패: 422 (FastAPI/Pydantic 기본 동작)
- 예상치 못한 에러: 글로벌 exception_handler로 Exception catch → 500 + ErrorResponse(code='INTERNAL_ERROR') + 스택트레이스 로그

### Claude's Discretion
- 서비스 함수 내부 세부 구조 (헬퍼 함수 분리 여부)
- Background Summary용 Gemini 호출 시 response_schema 사용 여부
- 글로벌 예외 핸들러의 정확한 구현 방식 (미들웨어 vs exception_handler 데코레이터)
- 프롬프트에 맥락 주입 시 정확한 포매팅 (Phase 2 프롬프트 빌더와 통합 방식)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/routers/meal.py`: POST /process-meal stub — Phase 3에서 서비스 호출로 교체
- `app/routers/recommend.py`: POST /recommend stub — Phase 3에서 서비스 호출로 교체
- `app/schemas/meal.py`: ProcessMealRequest, MealAnalysisData — 요청/응답 모델 확립
- `app/schemas/recommend.py`: RecommendRequest, RecommendationData — 요청/응답 모델 확립
- `app/schemas/common.py`: UserProfile, SuccessResponse, ErrorResponse — envelope 패턴 확립
- `app/clients/embedding.py`: EmbeddingClient.embed() — 384-dim, async threadpool
- `app/clients/pinecone.py`: PineconeClient.upsert(), search() — namespace 기반
- `app/clients/gemini.py`: GeminiClient.generate() — tenacity retry, response_schema
- `app/prompts/meal.py`, `app/prompts/recommend.py`: Mode 7/8 프롬프트 빌더

### Established Patterns
- 4계층 구조: routers → services → clients → core
- pydantic-settings 싱글턴: Settings via lru_cache
- app.state: 클라이언트 인스턴스 저장 (lifespan에서 초기화)
- 에러 응답: {status: "error", error: {code, message}} envelope

### Integration Points
- `app/services/__init__.py`: 빈 상태 — meal_service, recommend_service, background_summary 추가
- `app/routers/meal.py`: stub → service 호출로 교체
- `app/routers/recommend.py`: stub → service 호출로 교체
- `app/prompts/`: summary.py 추가 (요약 전용 프롬프트)
- `app/main.py`: 글로벌 예외 핸들러 등록

</code_context>

<specifics>
## Specific Ideas

- Background Summary는 응답 반환 후 실행되어야 함 — FastAPI BackgroundTasks 활용
- Pinecone 검색 실패가 전체 요청을 블록하면 안 됨 — graceful degradation 필수
- 첫 사용자(맥락 0건)도 정상 응답을 받아야 함 — 빈 맥락 처리 중요
- 프롬프트 빌더에 맥락 주입 파라미터 추가 필요 (Phase 2 빌더 확장)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-endpoints-and-memory*
*Context gathered: 2026-03-22*
