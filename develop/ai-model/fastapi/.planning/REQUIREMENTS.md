# Requirements: FastAPI AI Hub

**Defined:** 2026-03-21
**Core Value:** 사용자의 운동/식단 데이터 기반 개인화 AI 응답 + 벡터 메모리 축적으로 맥락 품질 지속 향상

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation

- [x] **FOUND-01**: FastAPI 프로젝트 4계층 구조 설정 (routers/services/clients/core)
- [x] **FOUND-02**: Pydantic 요청/응답 스키마 정의 (8모드 전체 JSON 규격 포함)
- [x] **FOUND-03**: pydantic-settings 기반 환경변수 관리 (API 키, Pinecone URL, WAS URL 등)
- [x] **FOUND-04**: FastAPI lifespan 이벤트로 클라이언트 초기화 (Pinecone, httpx, 임베딩 모델)

### Pinecone Integration

- [ ] **PINE-01**: PineconeAsyncio 클라이언트 연동 (async 검색/저장)
- [ ] **PINE-02**: namespace 기반 사용자 격리 (user_id별 namespace 강제)
- [ ] **PINE-03**: 벡터 검색 (user_id + 메시지 기반 맥락 검색, 결과 반환)
- [ ] **PINE-04**: 벡터 저장 (임베딩 값 + user_id + 요약 데이터 upsert)

### Embedding

- [ ] **EMBD-01**: sentence-transformers multilingual 모델 로딩 (paraphrase-multilingual-MiniLM-L12-v2, 768-dim)
- [ ] **EMBD-02**: 텍스트 임베딩 생성 (run_in_threadpool로 event loop 블록 방지)
- [ ] **EMBD-03**: Pinecone 인덱스 dimension과 임베딩 모델 dimension 일치 보장

### Gemini Flash

- [ ] **GEMI-01**: google-genai SDK 기반 Gemini Flash 클라이언트 구현
- [ ] **GEMI-02**: 재시도 로직 (429 에러 대응, exponential backoff + jitter)
- [ ] **GEMI-03**: 모드별 시스템 지시사항 프롬프트 관리 (JSON 출력 형식 지정)
- [ ] **GEMI-04**: Mode 7 (식단 기록) 프롬프트: 칼로리 분석 + 간결한 피드백 메시지
- [ ] **GEMI-05**: Mode 8 (추천 기능) 프롬프트: 운동/식단 추천 + 소모/섭취 칼로리

### Router AI

- [x] **ROUT-01**: LLM 기반 의도 분류 모듈 구현 (6가지 모드: 단순대화/플랜작성/플랜수정/식단작성/식단수정/DB수정)
- [x] **ROUT-02**: Router 시스템 지침서 프롬프트 적용 (JSON 출력: mode + reason)
- [x] **ROUT-03**: Router AI 단독 테스트 가능한 인터페이스

### Meal Recording (Mode 7)

- [ ] **MEAL-01**: POST /process-meal 엔드포인트 구현
- [ ] **MEAL-02**: 요청 처리: user_id, user_profile, user_instruction, user_message 수신
- [ ] **MEAL-03**: Pinecone 벡터 검색 (사용자 맥락 조회)
- [ ] **MEAL-04**: Gemini Flash 호출 (식단 분석 → 칼로리 + 메시지 반환)
- [ ] **MEAL-05**: 응답 형식: {status, data: {calories, message}}

### Recommendation (Mode 8)

- [ ] **RECOM-01**: POST /recommend 엔드포인트 구현
- [ ] **RECOM-02**: 요청 처리: user_id, user_profile, user_instruction 수신
- [ ] **RECOM-03**: Pinecone 벡터 검색 (사용자 맥락 조회)
- [ ] **RECOM-04**: Gemini Flash 호출 (운동/식단 추천 생성)
- [ ] **RECOM-05**: 응답 형식: {status, data: {recommended_exercise: {name, burn_calories}, recommended_meal: {name, calories}}}

### Background Summary

- [ ] **BGSM-01**: BackgroundTasks 기반 비동기 메모리 파이프라인 구현
- [ ] **BGSM-02**: Gemini Flash로 질문+답변 요약 생성
- [ ] **BGSM-03**: 요약 텍스트 임베딩 생성 (FastAPI 자체)
- [ ] **BGSM-04**: Pinecone에 벡터 임베딩 + user_id + 요약 + timestamp 저장
- [ ] **BGSM-05**: 에러 발생 시 로깅 (무음 실패 방지)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### AI Chat (Mode 1-6)

- **CHAT-01**: POST /ai-chat 엔드포인트 구현
- **CHAT-02**: 병렬 처리 (asyncio.gather: Router AI 의도분류 + Vector DB 맥락검색)
- **CHAT-03**: 조건부 WAS 리스트 요청 (Mode 3: 운동 리스트, Mode 5: 식단 리스트)
- **CHAT-04**: 8모드별 정형화 JSON 응답 생성
- **CHAT-05**: Mode 6 DB 수정 시 db_update 필드 포함, 프론트에는 message만 노출

### Error Handling

- **ERRH-01**: 글로벌 에러 핸들러 (일관적 에러 응답 포맷)
- **ERRH-02**: 구조화 로깅 (structlog/loguru)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Critic (검증 모듈) | v1 복잡도 관리, 추후 필요 시 추가 |
| Frontend (Next.js) | 별도 팀/브랜치 담당 |
| Backend WAS (Node.js) | 별도 팀/브랜치 담당 |
| DB Server 직접 접근 | WAS를 통해 간접 접근 |
| 실시간 스트리밍 (WebSocket) | WAS REST 계약 위반, 이점 없음 |
| 의료/임상 진단 | 건강 도메인 법적 리스크 (ECRI 2026 경고) |
| 전체 대화 히스토리 주입 | RAG 검색으로 대체 (토큰 효율) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Complete |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Pending |
| PINE-01 | Phase 2 | Pending |
| PINE-02 | Phase 2 | Pending |
| PINE-03 | Phase 2 | Pending |
| PINE-04 | Phase 2 | Pending |
| EMBD-01 | Phase 2 | Pending |
| EMBD-02 | Phase 2 | Pending |
| EMBD-03 | Phase 2 | Pending |
| GEMI-01 | Phase 2 | Pending |
| GEMI-02 | Phase 2 | Pending |
| GEMI-03 | Phase 2 | Pending |
| GEMI-04 | Phase 2 | Pending |
| GEMI-05 | Phase 2 | Pending |
| ROUT-01 | Phase 2 | Complete |
| ROUT-02 | Phase 2 | Complete |
| ROUT-03 | Phase 2 | Complete |
| MEAL-01 | Phase 3 | Pending |
| MEAL-02 | Phase 3 | Pending |
| MEAL-03 | Phase 3 | Pending |
| MEAL-04 | Phase 3 | Pending |
| MEAL-05 | Phase 3 | Pending |
| RECOM-01 | Phase 3 | Pending |
| RECOM-02 | Phase 3 | Pending |
| RECOM-03 | Phase 3 | Pending |
| RECOM-04 | Phase 3 | Pending |
| RECOM-05 | Phase 3 | Pending |
| BGSM-01 | Phase 3 | Pending |
| BGSM-02 | Phase 3 | Pending |
| BGSM-03 | Phase 3 | Pending |
| BGSM-04 | Phase 3 | Pending |
| BGSM-05 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation (coarse granularity: 3 phases)*
