# FastAPI AI Hub

## What This Is

헬스/운동 추천 서비스의 AI 오케스트레이션 허브. Next.js(Front) + Node.js(Backend) 구조의 WAS로부터 REST API 요청을 받아, Vector DB(Pinecone) 검색, Router AI(LLM 기반 의도 분류), Gemini Flash(생성/분석)를 조합하여 식단 기록 분석, 운동/식단 추천, AI 채팅(8모드) 기능을 제공한다. 모든 응답은 비동기 Background Summary 파이프라인을 통해 벡터 메모리로 축적된다.

## Core Value

사용자의 운동/식단 데이터를 기반으로 개인화된 AI 응답을 정확하고 빠르게 제공하는 것. 모든 상호작용은 벡터 메모리로 축적되어 맥락 기반 응답 품질이 지속적으로 향상된다.

## Current Milestone: v1.1 AI Chat Pipeline

**Goal:** POST /ai-chat 엔드포인트를 통해 8모드 전체 AI 채팅 파이프라인을 구현하고, WAS 통신 및 에러 핸들링을 고도화한다.

**Target features:**
- POST /ai-chat: 8모드 AI 채팅 파이프라인 (Router AI + Vector DB + Gemini Flash)
- WAS REST 통신 인터페이스 (모드 3/5 조건부 리스트 요청)
- 글로벌 에러 핸들러 고도화 (구조화 로깅)

## Requirements

### Validated

- ✓ FastAPI 서버 기본 구조 및 프로젝트 설정 — v1.0
- ✓ POST /process-meal: 식단 기록 분석 (Vector DB 검색 + Gemini Flash 칼로리 분석) — v1.0
- ✓ POST /recommend: 운동/식단 추천 (Vector DB 검색 + Gemini Flash 추천 생성) — v1.0
- ✓ Pinecone Vector DB 연동 (검색 + 저장) — v1.0
- ✓ Gemini Flash API 연동 (분석/추천/채팅 생성) — v1.0
- ✓ Router AI (LLM 기반 의도 분류 모듈) — v1.0
- ✓ Background Summary: 비동기 메모리 저장 (LLM 요약 + FastAPI 자체 임베딩 생성 + Pinecone 저장) — v1.0

### Active

- [ ] POST /ai-chat: AI 채팅 (Router AI 의도분류 + Vector DB 맥락검색 병렬 처리 + 조건부 WAS 리스트 요청 + Gemini Flash 8모드 정형화)
- [ ] WAS(Node.js) REST 통신 인터페이스
- [ ] 글로벌 에러 핸들러 고도화 (구조화 로깅)

### Out of Scope

- Critic (검증 모듈) — v1에서는 구현하지 않음, 추후 필요 시 추가
- Frontend (Next.js) — 별도 팀/브랜치에서 담당
- Backend WAS (Node.js) — 별도 팀/브랜치에서 담당
- DB Server 직접 접근 — WAS를 통해 간접 접근
- 실시간 스트리밍 (WebSocket) — WAS REST 계약 위반, 이점 없음
- 의료/임상 진단 — 건강 도메인 법적 리스크

## Context

- 캡스톤 프로젝트 (팀 프로젝트)
- 전체 아키텍처: Front(Next.js) -> Back Area(Node.js WAS + DB Server) -> AI Area(FastAPI Hub + Operations)
- AI Area 내 Operations: Vector DB(Pinecone), Router AI, Gemini Flash
- WAS <-> FastAPI Hub 통신: REST API (HTTP)
- v1.0 shipped: 3,000 LOC Python (1,014 app + 1,970 tests), 30 requirements complete
- Tech stack: FastAPI, Pinecone, Gemini Flash, sentence-transformers (384-dim)
- 임베딩 모델: paraphrase-multilingual-MiniLM-L12-v2 (384차원, 초기 768 예상에서 변경)
- 워커 AI 인풋 우선순위: 사용자 메시지(1순위) > 사용자 지시사항(2순위) > 시스템 지시사항(3순위)
- db_modified_flag: FastAPI가 모드별 결정 (none/exercise/meal/profile)

## Constraints

- **Tech Stack**: FastAPI (Python) — AI 서비스 허브
- **LLM**: Gemini Flash — Google AI 모델
- **Vector DB**: Pinecone — 클라우드 관리형
- **통신**: REST API — WAS(Node.js)와 HTTP 기반 통신
- **범위**: AI Area만 담당 — Front/Back은 별도 팀

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pinecone 사용 | 클라우드 관리형으로 운영 부담 최소화 | ✓ Good — namespace 격리로 사용자별 벡터 관리 |
| Gemini Flash 선택 | 속도와 비용 효율성 | ✓ Good — Mode 7/8 JSON 스키마 출력 안정 |
| Critic 제외 | v1 복잡도 관리, 핵심 기능 우선 | ✓ Good — v1 범위 관리에 효과적 |
| FastAPI 자체 임베딩 생성 | 외부 임베딩 서비스 의존 최소화 | ✓ Good — run_in_threadpool로 블록 방지 |
| 비동기 Background Summary | 응답 속도와 메모리 저장을 분리 | ✓ Good — 에러 격리 (무음 실패) |
| 384-dim 임베딩 (MiniLM-L12-v2) | 초기 768-dim 가정 수정, 실제 모델 출력 기반 | ✓ Good — Pinecone 인덱스와 일치 |
| _fetch_context 인라인 (서비스별 별도) | meal/recommend 서비스 간 낮은 결합도 | ✓ Good — 독립적 변경 가능 |
| db_modified_flag FastAPI 결정 | Gemini에 맡기면 불안정, 모드별 매핑이 직관적 | — Pending |

---
*Last updated: 2026-03-22 after v1.1 milestone start*
