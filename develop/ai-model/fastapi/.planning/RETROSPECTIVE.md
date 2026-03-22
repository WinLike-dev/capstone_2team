# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-22
**Phases:** 3 | **Plans:** 10 | **Sessions:** ~5

### What Was Built
- FastAPI 4계층 구조 (routers/services/clients/core) + Pydantic 스키마
- Pinecone Vector DB 클라이언트 (namespace 기반 사용자 격리)
- Gemini Flash 클라이언트 + Mode 7/8 프롬프트 + exponential backoff
- Router AI 의도분류 모듈 (6모드)
- `/process-meal`, `/recommend` 서비스 파이프라인
- Background Summary 비동기 메모리 파이프라인

### What Worked
- Phase 분리 전략 (Foundation → Integrations → Endpoints)이 의존성 충돌 없이 깔끔하게 진행됨
- TDD 방식이 Phase 2/3에서 효과적 — 테스트 먼저 작성 후 구현하니 통합 시 문제 거의 없음
- Stub 엔드포인트를 Phase 1에서 만들고 Phase 3에서 교체하는 패턴이 인터페이스 안정성 보장
- Wave 기반 병렬 실행으로 Phase 3의 plan 03-02, 03-03 동시 처리

### What Was Inefficient
- ROADMAP.md 체크박스/진행률 추적이 자동 업데이트에서 누락되는 경우 발생 (Phase 2 체크박스, Traceability Pending)
- 임베딩 모델 dimension 초기 가정(768)이 틀렸음 → 실제 384-dim으로 Phase 2에서 수정
- Phase 2의 5개 plan 중 일부에서 env-var 관련 테스트 실패가 Phase 3까지 지속 (해결 안 됨)

### Patterns Established
- `_fetch_context()` 인라인 패턴: 서비스별 독립적 Pinecone+embed 컨텍스트 조회
- `context_text` 파라미터 주입: 프롬프트 빌더에 검색된 맥락 전달
- Background Summary 에러 격리: try/except + logger.exception, 절대 re-raise 안 함
- `ASGITransport(raise_app_exceptions=False)`: httpx 0.28에서 글로벌 예외 핸들러 테스트

### Key Lessons
1. 임베딩 모델 dimension은 반드시 실제 모델 출력으로 확인 — 문서 기반 가정 위험
2. 추적 메타데이터(체크박스, 진행률)는 실행 완료 시 자동 업데이트가 완전하지 않으면 마일스톤 완료 시 수동 정리 필요
3. Stub→Production 교체 패턴이 효과적 — 인터페이스를 먼저 확정하고 구현을 나중에 채우는 전략

### Cost Observations
- Model mix: ~20% opus, ~80% sonnet (executor는 sonnet, orchestrator는 opus)
- Sessions: ~5 sessions over 7 days
- Notable: Wave 병렬 실행이 Phase 3 실행 시간을 ~40% 절감

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~5 | 3 | Initial build — TDD + wave parallelism established |

### Cumulative Quality

| Milestone | Tests | LOC | App LOC |
|-----------|-------|-----|---------|
| v1.0 | 60+ | 3,000 | 1,014 |

### Top Lessons (Verified Across Milestones)

1. Stub→Production 교체 패턴은 인터페이스 안정성을 보장하면서 점진적 구현 가능
2. 임베딩 모델 등 외부 의존성의 실제 사양은 문서가 아닌 코드/실행으로 확인
