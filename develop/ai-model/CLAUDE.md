# 헬스 메이트 AI 라우터 - CLAUDE.md

## 프로젝트 개요
AI 헬스케어 서비스 '헬스 메이트'의 백엔드 AI 라우터 시스템.
LangGraph StateGraph를 사용하여 사용자 입력 의도를 파악하고,
도메인 전문가(운동/식단)를 거쳐 맞춤형 플랜을 생성·검증하는 파이프라인.

## 기술 스택
- **Framework**: FastAPI + LangGraph + LangChain
- **LLM (전문가 노드)**: `gemini-3-flash-preview` — Exercise Expert, Diet Expert, Plan Draft
- **LLM (라우터 노드)**: `gemini-2.5-flash-lite` — Super Agent, Evaluator, Reask
- **Python**: 3.14
- **주요 패키지**: `langgraph`, `langchain-google-genai`, `fastapi`, `uvicorn`, `python-dotenv`

## 디렉토리 구조
```
develop/ai-model/
├── main.py                  # FastAPI 앱 진입점
├── requirements.txt
├── .env                     # GOOGLE_API_KEY (UTF-8 저장 필수)
├── .env.example
├── CLAUDE.md
└── app/
    ├── graph/
    │   ├── state.py         # HealthMateState (TypedDict)
    │   ├── nodes.py         # 6개 노드 + LLM 인스턴스
    │   └── pipeline.py      # StateGraph 조립 및 컴파일
    └── api/
        └── routes.py        # POST /api/v1/health-plan 엔드포인트
```

## 파이프라인 흐름
```
START → [Super Agent] → confidence < 0.7 → [Reask] → END
                      → intent='운동'    → [Exercise Expert] → [Plan Draft] → [Evaluator] → is_safe=True  → END
                      → intent='식단'    → [Diet Expert]     → [Plan Draft] → [Evaluator] → is_safe=False → [Reask] → END
```

## 노드 설명

| 노드 | 역할 | 모델 |
|---|---|---|
| Super Agent | 의도(운동/식단) + 확신도 파악. Pydantic Structured Output 사용 | `gemini-2.5-flash-lite` |
| Exercise Expert | 헬스 트레이너 페르소나. 운동 조언만 생성 (식단 내용 배제) | `gemini-3-flash-preview` |
| Diet Expert | 영양사 페르소나. 식단 조언만 생성 (운동 내용 배제) | `gemini-3-flash-preview` |
| Plan Draft | 전문가 조언 → 실행 가능한 플랜 초안. intent 기반 도메인 제한 | `gemini-3-flash-preview` |
| Evaluator | 환각/위험 가이드 자체 검증. Pydantic Structured Output 사용 | `gemini-2.5-flash-lite` |
| Reask | 확신도 부족 or 평가 FAIL 시 재질문 안내 메시지 생성 | `gemini-2.5-flash-lite` |

## Conditional Edge 라우팅 규칙
- **Super Agent 이후**
  - `confidence < 0.7` → Reask
  - `confidence >= 0.7` + `intent='운동'` → Exercise Expert
  - `confidence >= 0.7` + `intent='식단'` → Diet Expert
- **Evaluator 이후**
  - `is_safe=True` → END (final_plan 확정)
  - `is_safe=False` → Reask → END

## State 스키마 (HealthMateState)
```python
user_input    : str           # 사용자 원문 입력
intent        : str | None    # '운동' 또는 '식단'
confidence    : float | None  # 의도 확신도 (0.0 ~ 1.0)
expert_advice : str | None    # 전문가 조언
draft_plan    : str | None    # 플랜 초안
is_safe       : bool | None   # 평가 통과 여부
final_plan    : str | None    # 최종 승인된 플랜
error_message : str | None    # 재질문 안내 메시지
```

## API 엔드포인트
- `POST /api/v1/health-plan` — 사용자 입력 → 맞춤형 플랜 반환
- `GET  /api/v1/health`      — 서버 상태 확인

## 환경 설정
```bash
# .env 파일 (UTF-8 인코딩으로 저장)
GOOGLE_API_KEY=your_google_api_key_here
```
> **.env는 반드시 UTF-8로 저장.** UTF-16 저장 시 python-dotenv가 파싱 실패함.

## 실행 방법
```bash
cd develop/ai-model
pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8000
# 포트 충돌 시: --port 8001
```
Swagger UI: `http://localhost:8000/docs`

## 제외된 노드 (추후 구현 예정)
- 검색 라우터
- 탐색 횟수 초과 여부
- Web Search
- RAG Search (Pinecone 연동)
- 문서 평가

현재는 `[전문가 노드] → [Plan Draft]`로 Edge 직접 연결.

## 주요 구현 이슈 및 해결
| 이슈 | 원인 | 해결 |
|---|---|---|
| `gemini-2.0-flash` 404 오류 | 신규 API 키에서 사용 불가 | `gemini-2.5-flash-lite`로 대체 |
| `.env` 파싱 실패 | 파일이 UTF-16으로 저장됨 | UTF-8로 재저장 |
| `gemini-3-flash-preview` 응답이 `list[dict]` 형태 | 모델이 content를 블록 형태로 반환 | `_extract_text()` 헬퍼로 텍스트 추출 |
| 운동 질문에 식단 답변 포함 | 전문가/플랜 프롬프트에 도메인 제한 없음 | 각 노드 프롬프트에 타 도메인 배제 명시 |
