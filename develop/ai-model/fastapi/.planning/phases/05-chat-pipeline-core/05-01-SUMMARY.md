---
phase: 05-chat-pipeline-core
plan: 01
subsystem: api
tags: [gemini, pinecone, asyncio, worker-ai, chat-pipeline, router-ai, background-summary]

# Dependency graph
requires:
  - phase: 04-infrastructure
    provides: RouterClient.classify(), GeminiClient.generate(), PineconeClient, EmbeddingClient, WASClient
  - phase: 03-background-summary
    provides: run_background_summary()
  - phase: 02-schemas
    provides: AiChatRequest, AiChatResponse, AiChatData, get_db_modified_flag(), UserProfile
provides:
  - build_worker_system_prompt() — 모드(1-8)별 Worker AI 시스템 프롬프트 빌더
  - handle_ai_chat() — Chat Pipeline 오케스트레이터 (asyncio.gather 병렬 실행)
affects: [05-chat-pipeline-core/05-02, 06-mode-handlers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio.gather로 Router AI + Vector DB context 병렬 실행"
    - "모드별 db_modified_flag는 FastAPI가 결정 (Gemini 아님)"
    - "_get_worker_response_schema() 헬퍼로 Phase 6 모드별 스키마 교체 준비"
    - "Router AI 실패 시 mode=1 fallback (graceful degradation)"

key-files:
  created:
    - app/prompts/worker.py
    - app/services/chat_service.py
    - tests/test_chat_service.py
  modified: []

key-decisions:
  - "build_worker_system_prompt() 프롬프트 조립 순서: 사용자 지시사항 > 시스템 지시사항 > 사용자 프로필 > 이전 맥락 (CHAT-12)"
  - "Phase 5에서는 SimpleAnswerOutput 단일 스키마 사용, Phase 6에서 모드별 스키마로 교체 예정"
  - "asyncio.gather 첫 번째 coroutine 실패 시 전체 except로 mode=1 fallback 처리"

patterns-established:
  - "TDD RED(test) → GREEN(feat) 커밋 분리 패턴 유지"
  - "_fetch_context() 헬퍼는 meal_service.py 패턴과 동일 — graceful degradation"

requirements-completed: [CHAT-01, CHAT-02, CHAT-11, CHAT-12, CHAT-13]

# Metrics
duration: 4min
completed: 2026-03-22
---

# Phase 5 Plan 01: Chat Pipeline Core Summary

**asyncio.gather로 Router AI + Vector DB를 병렬 실행하고 모드별 db_modified_flag를 결정하는 Chat Pipeline 오케스트레이터 + 8모드 Worker AI 시스템 프롬프트 빌더 구현**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-22T08:19:52Z
- **Completed:** 2026-03-22T08:24:07Z
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments

- `build_worker_system_prompt()` 구현 — 8개 모드 지원, user_instruction 없으면 섹션 생략, _format_user_profile()로 None 필드 제외
- `handle_ai_chat()` Chat Pipeline 오케스트레이터 구현 — asyncio.gather 병렬 실행, db_modified_flag 결정, Background Summary 비동기 등록
- TDD 7개 유닛 테스트 전체 통과 (병렬 실행, db_flag 모드별, user_instruction 생략, background task, router fallback)

## Task Commits

1. **Task 1: Worker AI 시스템 프롬프트 빌더** - `fb79719` (feat)
2. **Task 2: TDD RED — 실패 테스트 작성** - `4ea33fb` (test)
3. **Task 2: TDD GREEN + 테스트 수정** - `4635d69` (feat)

## Files Created/Modified

- `app/prompts/worker.py` — 8모드 Worker AI 시스템 프롬프트 빌더, _MODE_INSTRUCTIONS 딕셔너리, _format_user_profile() 헬퍼
- `app/services/chat_service.py` — Chat Pipeline 오케스트레이터, asyncio.gather 병렬 실행, WAS 조건부 분기, Background Summary 등록
- `tests/test_chat_service.py` — 7개 유닛 테스트 (TDD)

## Decisions Made

- `build_worker_system_prompt()` 섹션 헤더 패턴 `"사용자 지시사항: "` (콜론+공백)으로 user_instruction 존재 여부 구분 — 공통 규칙 본문에 "사용자 지시사항" 단어가 포함되어 있어 섹션 헤더 패턴으로 구별
- Phase 5에서는 `SimpleAnswerOutput(answer: str)` 단일 스키마로 통일, `_get_worker_response_schema()` 헬퍼에 TODO(Phase 6) 마킹

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 테스트 assertion 패턴 수정**
- **Found during:** Task 2 (TDD GREEN)
- **Issue:** 테스트에서 `"사용자 지시사항"` 미포함 확인 시 공통 규칙 본문에도 해당 단어가 등장하여 False Positive 발생
- **Fix:** `"사용자 지시사항: "` (콜론+공백) 패턴으로 변경 — 섹션 헤더와 본문 텍스트 구별
- **Files modified:** tests/test_chat_service.py
- **Verification:** `python -m pytest tests/test_chat_service.py` — 7/7 통과
- **Committed in:** 4635d69 (Task 2 feat commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** 테스트 assertion 패턴 보정. 기능 로직 변경 없음.

## Issues Encountered

None — 실패 assert 패턴이 공통 규칙 본문 텍스트와 충돌하는 문제를 Rule 1로 즉시 수정.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `handle_ai_chat()` 오케스트레이터 완성 — Phase 5 Plan 02에서 `/ai-chat` 라우터 엔드포인트 연결 준비
- `_get_worker_response_schema()` 헬퍼에 Phase 6 모드별 스키마 교체 진입점 마련
- mode 3/5 WAS 조건부 분기 구현 완료 — Phase 6에서 모드별 핸들러로 이전 예정

## Self-Check: PASSED

- FOUND: app/prompts/worker.py
- FOUND: app/services/chat_service.py
- FOUND: tests/test_chat_service.py
- FOUND: .planning/phases/05-chat-pipeline-core/05-01-SUMMARY.md
- FOUND commit: fb79719 (feat: Worker AI 시스템 프롬프트 빌더)
- FOUND commit: 4ea33fb (test: 실패 테스트 작성)
- FOUND commit: 4635d69 (feat: Chat Pipeline 오케스트레이터)

---
*Phase: 05-chat-pipeline-core*
*Completed: 2026-03-22*
