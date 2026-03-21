# Phase 1: Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

FastAPI 서버 구조 확립, pydantic-settings 기반 환경변수 관리, WAS와의 API 계약(Pydantic 스키마) 코드화, /health 엔드포인트 구현, /process-meal과 /recommend 스텁 엔드포인트 구현. 실제 외부 서비스 연동(Gemini, Pinecone, Embedding)은 Phase 2에서 수행.

</domain>

<decisions>
## Implementation Decisions

### API 스키마 설계
- UserProfile은 통합 모델로 구현: 모든 필드를 Optional로 두고 /process-meal, /recommend에서 공유. WAS가 보내는 대로 받되 없는 필드는 None 처리
- Gemini 응답도 Pydantic 모델로 정의: Phase 2에서 파싱/검증에 활용
- v2 /ai-chat 스키마는 Phase 1에서 정의하지 않음 — v2 마일스톤에서 추가
- 스키마 파일은 도메인별 분리: schemas/meal.py, schemas/recommend.py, schemas/common.py 등

### 에러 응답 규격
- 통일된 envelope 포맷: `{status: "error", error: {code: "ERROR_CODE", message: "설명"}}`
- HTTP 상태코드는 단순화: 200 성공, 400 클라이언트 오류, 500 서버 오류 (3가지)
- 외부 서비스 에러 코드 구분: GEMINI_ERROR, PINECONE_ERROR, EMBEDDING_ERROR 등으로 error.code에 명시하여 WAS가 에러 원인 파악 가능

### 환경변수/설정
- Phase 1에서 전체 환경변수 정의: GEMINI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME, WAS_BASE_URL 등 Phase 2-3에서 쓸 변수까지 모두 Settings 클래스에 포함
- .env + .env.example 방식: .env는 gitignore, .env.example은 커밋하여 팀원이 필요한 변수 확인 가능
- 필수 환경변수 누락 시 서버 시작 시점에 즉시 종료: pydantic-settings ValidationError로 명확한 에러 메시지 출력

### v1 스텁 엔드포인트
- /process-meal, /recommend를 스텁으로 구현: 요청 스키마 검증만 동작하고 목 데이터 반환
- 스텁 응답에 별도 표시 없음: 실제 응답과 동일한 포맷. Phase 3에서 목 데이터만 실제로 교체

### Claude's Discretion
- 4계층 디렉토리 구조의 세부 파일 배치 (routers/services/clients/core)
- lifespan 이벤트 내부 초기화 순서
- 로깅 설정 방식

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 없음 (그린필드 프로젝트)

### Established Patterns
- 없음 (첫 코드 작성)

### Integration Points
- WAS(Node.js) → FastAPI: REST API (POST /process-meal, POST /recommend)
- 참고 문서: docs/DataFormat_2_ai.md (요청/응답 JSON 규격), docs/DataFormat_3_ai.md (ai-chat 규격, v2)
- 참고 문서: docs/ai_io_instruction.txt (8모드 I/O 명세)

</code_context>

<specifics>
## Specific Ideas

- /process-meal의 user_profile에는 medical_history, allergies 포함 / /recommend에는 activity_level 포함 (docs/DataFormat_2_ai.md 기준)
- 성공 응답 envelope: `{status: "success", data: {...}}`
- 에러 응답 envelope: `{status: "error", error: {code: "...", message: "..."}}`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-22*
