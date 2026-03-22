# Requirements: FastAPI AI Hub

**Defined:** 2026-03-22
**Core Value:** 사용자의 운동/식단 데이터 기반 개인화 AI 응답 + 벡터 메모리 축적으로 맥락 품질 지속 향상

## v1.1 Requirements

Requirements for AI Chat Pipeline milestone. Each maps to roadmap phases.

### AI Chat

- [ ] **CHAT-01**: POST /ai-chat 엔드포인트가 사용자 메시지를 받아 Router AI로 모드(1~6)를 분류한다
- [ ] **CHAT-02**: Router AI 분류와 Vector DB 맥락검색이 병렬로 실행된다
- [ ] **CHAT-03**: 모드 1(단순대화) — 공통값 + 라우터 결과로 Gemini가 answer JSON 반환
- [ ] **CHAT-04**: 모드 2(플랜 작성) — 공통값 + 라우터 결과로 Gemini가 운동 계획 JSON 배열 반환
- [ ] **CHAT-05**: 모드 3(플랜 수정) — WAS에서 현재 운동 리스트 조회 후 Gemini가 수정된 계획 반환
- [ ] **CHAT-06**: 모드 4(식단 작성) — 공통값 + 라우터 결과로 Gemini가 식단 JSON 배열 반환
- [ ] **CHAT-07**: 모드 5(식단 수정) — WAS에서 현재 식단 리스트 조회 후 Gemini가 수정된 식단 반환
- [ ] **CHAT-08**: 모드 6(사용자 DB 수정) — 공통값으로 Gemini가 updated_fields JSON 반환
- [ ] **CHAT-09**: 모드 7(식단 기록) — 공통값으로 Gemini가 칼로리/영양소 JSON 반환
- [ ] **CHAT-10**: 모드 8(추천) — 공통값으로 Gemini가 운동3+식단2 추천 JSON 반환
- [ ] **CHAT-11**: 모드별 db_modified_flag를 FastAPI가 결정하여 응답에 포함 (none/exercise/meal/profile)
- [ ] **CHAT-12**: 워커 AI 인풋 우선순위 반영 (사용자 메시지 > 사용자 지시사항 > 시스템 지시사항)
- [ ] **CHAT-13**: 응답 후 Background Summary 파이프라인으로 벡터 메모리 축적

### WAS 통신

- [ ] **WAS-01**: WAS HTTP 클라이언트 모듈 (httpx 기반, 운동/식단 리스트 조회)
- [ ] **WAS-02**: 모드 3 처리 시 WAS에 현재 운동 리스트 요청
- [ ] **WAS-03**: 모드 5 처리 시 WAS에 현재 식단 리스트 요청
- [ ] **WAS-04**: 최종 응답에 db_modified_flag + Gemini 결과를 조합하여 WAS에 반환

### 에러 핸들링

- [ ] **ERR-01**: 글로벌 에러 핸들러 (구조화 JSON 에러 응답)
- [ ] **ERR-02**: 구조화 로깅 (요청 ID, 모드, 처리 시간 포함)

## v2 Requirements

Deferred to future release.

### Advanced Features

- **ADV-01**: Critic (검증 모듈) — AI 응답 품질 검증
- **ADV-02**: 라우터 AI를 메인 AI로 승격 (시간 소요 작업 전문가 AI 분기)

## Out of Scope

| Feature | Reason |
|---------|--------|
| 실시간 스트리밍 (WebSocket) | WAS REST 계약 위반, 이점 없음 |
| Frontend/Backend 직접 구현 | 별도 팀 담당 |
| DB Server 직접 접근 | WAS를 통해 간접 접근 |
| 의료/임상 진단 | 건강 도메인 법적 리스크 |
| WAS 재시도/타임아웃 고도화 | v1.1은 조건부 요청만, 고도화는 추후 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHAT-01 | Phase 5 | Pending |
| CHAT-02 | Phase 5 | Pending |
| CHAT-03 | Phase 6 | Pending |
| CHAT-04 | Phase 6 | Pending |
| CHAT-05 | Phase 6 | Pending |
| CHAT-06 | Phase 6 | Pending |
| CHAT-07 | Phase 6 | Pending |
| CHAT-08 | Phase 6 | Pending |
| CHAT-09 | Phase 6 | Pending |
| CHAT-10 | Phase 6 | Pending |
| CHAT-11 | Phase 5 | Pending |
| CHAT-12 | Phase 5 | Pending |
| CHAT-13 | Phase 5 | Pending |
| WAS-01 | Phase 4 | Pending |
| WAS-02 | Phase 4 | Pending |
| WAS-03 | Phase 4 | Pending |
| WAS-04 | Phase 4 | Pending |
| ERR-01 | Phase 4 | Pending |
| ERR-02 | Phase 4 | Pending |

**Coverage:**
- v1.1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after v1.1 roadmap creation*
