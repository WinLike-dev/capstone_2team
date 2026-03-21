# FastAPI AI Hub

## What This Is

헬스/운동 추천 서비스의 AI 오케스트레이션 허브. Next.js(Front) + Node.js(Backend) 구조의 WAS로부터 REST API 요청을 받아, Vector DB(Pinecone) 검색, Router AI(LLM 기반 의도 분류), Gemini Flash(생성/분석)를 조합하여 식단 기록 분석, 운동/식단 추천, AI 채팅 기능을 제공한다.

## Core Value

사용자의 운동/식단 데이터를 기반으로 개인화된 AI 응답을 정확하고 빠르게 제공하는 것. 모든 상호작용은 벡터 메모리로 축적되어 맥락 기반 응답 품질이 지속적으로 향상된다.

## Requirements

### Validated

(None yet -- ship to validate)

### Active

- [ ] FastAPI 서버 기본 구조 및 프로젝트 설정
- [ ] POST /process-meal: 식단 기록 분석 (Vector DB 검색 + Gemini Flash 칼로리 분석)
- [ ] POST /recommend: 운동/식단 추천 (Vector DB 검색 + Gemini Flash 추천 생성)
- [ ] POST /ai-chat: AI 채팅 (Router AI 의도분류 + Vector DB 맥락검색 병렬 처리 + 조건부 WAS 리스트 요청 + Gemini Flash 8모드 정형화)
- [ ] Pinecone Vector DB 연동 (검색 + 저장)
- [ ] Gemini Flash API 연동 (분석/추천/채팅 생성)
- [ ] Router AI (LLM 기반 의도 분류 모듈)
- [ ] Background Summary: 비동기 메모리 저장 (LLM 요약 + FastAPI 자체 임베딩 생성 + Pinecone 저장)
- [ ] WAS(Node.js) REST 통신 인터페이스

### Out of Scope

- Critic (검증 모듈) -- v1에서는 구현하지 않음, 추후 필요 시 추가
- Frontend (Next.js) -- 별도 팀/브랜치에서 담당
- Backend WAS (Node.js) -- 별도 팀/브랜치에서 담당
- DB Server 직접 접근 -- WAS를 통해 간접 접근

## Context

- 캡스톤 프로젝트 (팀 프로젝트)
- 전체 아키텍처: Front(Next.js) -> Back Area(Node.js WAS + DB Server) -> AI Area(FastAPI Hub + Operations)
- AI Area 내 Operations: Vector DB(Pinecone), Router AI, Gemini Flash
- WAS <-> FastAPI Hub 통신: REST API (HTTP)
- 모든 엔드포인트는 응답 후 비동기로 Background Summary 수행 (요약 -> 임베딩 -> Pinecone 저장)
- 채팅 엔드포인트에서 질문 유형이 수적인 경우 WAS에 현재 리스트 요청하는 조건부 플로우 존재
- Gemini Flash는 8가지 모드별 정형화 데이터를 반환
- 벡터 임베딩 생성은 FastAPI 자체에서 수행

## Constraints

- **Tech Stack**: FastAPI (Python) -- AI 서비스 허브
- **LLM**: Gemini Flash -- Google AI 모델
- **Vector DB**: Pinecone -- 클라우드 관리형
- **통신**: REST API -- WAS(Node.js)와 HTTP 기반 통신
- **범위**: AI Area만 담당 -- Front/Back은 별도 팀

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pinecone 사용 | 클라우드 관리형으로 운영 부담 최소화 | -- Pending |
| Gemini Flash 선택 | 속도와 비용 효율성 | -- Pending |
| Critic 제외 | v1 복잡도 관리, 핵심 기능 우선 | -- Pending |
| FastAPI 자체 임베딩 생성 | 외부 임베딩 서비스 의존 최소화 | -- Pending |
| 비동기 Background Summary | 응답 속도와 메모리 저장을 분리 | -- Pending |

---
*Last updated: 2026-03-21 after initialization*
