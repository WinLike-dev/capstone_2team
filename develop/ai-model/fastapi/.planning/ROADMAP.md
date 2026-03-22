# Roadmap: FastAPI AI Hub

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-03-22)
- 🚧 **v1.1 AI Chat Pipeline** — Phases 4-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-03-22</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-03-21
- [x] Phase 2: Core Integrations (5/5 plans) — completed 2026-03-22
- [x] Phase 3: Endpoints and Memory (3/3 plans) — completed 2026-03-22

</details>

### 🚧 v1.1 AI Chat Pipeline (In Progress)

**Milestone Goal:** POST /ai-chat 엔드포인트를 통해 8모드 전체 AI 채팅 파이프라인을 구현하고, WAS 통신 및 에러 핸들링을 고도화한다.

- [ ] **Phase 4: Infrastructure** - 글로벌 에러 핸들러 + 구조화 로깅 + WAS HTTP 클라이언트
- [x] **Phase 5: Chat Pipeline Core** - Router AI + Vector DB 병렬처리 + db_modified_flag + Background Summary 연동 (completed 2026-03-22)
- [ ] **Phase 6: 8-Mode Gemini Handlers** - 모드별 Gemini 호출 및 JSON 출력 (모드 1~8 전체 구현)

## Phase Details

### Phase 4: Infrastructure
**Goal**: 에러 처리 일관성과 WAS 통신 기반이 완성되어 상위 파이프라인이 안전하게 의존할 수 있다
**Depends on**: Phase 3 (v1.0 완료)
**Requirements**: ERR-01, ERR-02, WAS-01, WAS-02, WAS-03, WAS-04
**Success Criteria** (what must be TRUE):
  1. 모든 예외가 구조화된 JSON 에러 응답으로 반환된다 (status, error_code, message 필드 포함)
  2. 모든 요청에 요청 ID, 처리 시간, 모드가 로그에 기록된다
  3. WAS HTTP 클라이언트가 모드 3 요청 시 운동 리스트를 조회하여 반환한다
  4. WAS HTTP 클라이언트가 모드 5 요청 시 식단 리스트를 조회하여 반환한다
  5. FastAPI가 db_modified_flag와 Gemini 결과를 조합한 최종 응답을 WAS에 반환한다
**Plans:** 2 plans
Plans:
- [ ] 04-01-PLAN.md — Custom exceptions + structured error handlers + request logging middleware
- [ ] 04-02-PLAN.md — WAS HTTP client + AI chat request/response schemas

### Phase 5: Chat Pipeline Core
**Goal**: POST /ai-chat가 Router AI 의도분류와 Vector DB 맥락검색을 병렬 실행하여 8모드 처리를 오케스트레이션한다
**Depends on**: Phase 4
**Requirements**: CHAT-01, CHAT-02, CHAT-11, CHAT-12, CHAT-13
**Success Criteria** (what must be TRUE):
  1. POST /ai-chat 요청이 Router AI를 통해 모드(1~6)로 분류된다
  2. Router AI 분류와 Vector DB 맥락검색이 동시에 실행된다 (순차 실행 아님)
  3. 각 모드에 대해 FastAPI가 db_modified_flag를 결정하여 응답에 포함한다 (none/exercise/meal/profile)
  4. 워커 AI 프롬프트가 사용자 메시지 > 사용자 지시사항 > 시스템 지시사항 순서로 구성된다
  5. 응답 후 Background Summary 파이프라인이 비동기로 벡터 메모리에 저장한다
**Plans:** 2/2 plans complete
Plans:
- [ ] 05-01-PLAN.md — Worker AI prompt builder + Chat pipeline orchestrator service
- [ ] 05-02-PLAN.md — POST /ai-chat router endpoint + main.py registration

### Phase 6: 8-Mode Gemini Handlers
**Goal**: 8개 모드 각각에 대해 Gemini Flash가 정형화된 JSON을 반환하며 모드별 WAS 조건부 통신이 동작한다
**Depends on**: Phase 5
**Requirements**: CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07, CHAT-08, CHAT-09, CHAT-10
**Success Criteria** (what must be TRUE):
  1. 모드 1(단순대화) 요청에 Gemini가 answer 필드를 포함한 JSON을 반환한다
  2. 모드 2(플랜 작성), 4(식단 작성) 요청에 Gemini가 운동/식단 JSON 배열을 반환한다
  3. 모드 3(플랜 수정)은 WAS 운동 리스트 조회 후, 모드 5(식단 수정)는 WAS 식단 리스트 조회 후 Gemini가 수정 결과를 반환한다
  4. 모드 6(사용자 DB 수정) 요청에 Gemini가 updated_fields JSON을 반환한다
  5. 모드 7(식단 기록), 8(추천) 요청에 Gemini가 칼로리/영양소 및 운동3+식단2 추천 JSON을 반환한다
**Plans:** 1 plan
Plans:
- [ ] 06-01-PLAN.md — 8모드 Gemini 응답 스키마 + 모드별 분기/파싱 로직

## Progress

**Execution Order:**
Phases execute in numeric order: 4 → 5 → 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-03-21 |
| 2. Core Integrations | v1.0 | 5/5 | Complete | 2026-03-22 |
| 3. Endpoints and Memory | v1.0 | 3/3 | Complete | 2026-03-22 |
| 4. Infrastructure | v1.1 | 0/2 | In progress | - |
| 5. Chat Pipeline Core | v1.1 | 2/2 | Complete | 2026-03-22 |
| 6. 8-Mode Gemini Handlers | v1.1 | 0/1 | Not started | - |
