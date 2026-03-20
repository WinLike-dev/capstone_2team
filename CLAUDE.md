# CLAUDE.md — AI Core 마이크로서비스 컨텍스트 가이드

> 이 문서는 AI 어시스턴트(Claude 등)가 본 프로젝트를 빠르게 이해하도록 작성된 **머신 리딩용 문서**입니다.

---

## 프로젝트 개요

**HealthMate** 헬스케어 앱의 AI Core 마이크로서비스.
FastAPI + LangChain + Google Gemini Flash 기반으로, **Router AI → Worker AI** 두 트랙 파이프라인을 구현합니다.
WAS(Node.js)에서 사용자 프로필과 메시지를 받아 모드별 구조화된 JSON 응답을 생성합니다.

---

## 담당 분리

| 구분 | 담당 | 상태 |
|------|------|------|
| Router AI 시스템 프롬프트 | Router AI 팀 | ✅ 완료 |
| Router AI 실행 로직 (`_run_router`) | Router AI 팀 | ✅ 완료 |
| 모드 3/5 백엔드 데이터 페치 | Router AI 팀 | ✅ 완료 (더미, TODO) |
| Worker AI 프롬프트 (`MODE1~8_SYSTEM`) | Worker AI 팀 | ⬜ 미구현 |
| Worker AI 실행 (`_call_worker_ai` 등) | Worker AI 팀 | ⬜ stub 상태 |
| 식단 기록 Worker AI | Worker AI 팀 | ⬜ stub 상태 |
| 추천 기능 알고리즘 | Worker AI 팀 | ⬜ stub 상태 |

---

## 디렉토리 구조

```
capstone_2team/
├── .gitignore
├── CLAUDE.md
└── develop/
    └── ai-model/
        └── ai_core/              ← AI 서비스 루트 (uvicorn 실행 기준 디렉토리)
            ├── main.py           # FastAPI 앱 엔트리포인트 + CORS + lifespan
            ├── config.py         # pydantic-settings 기반 환경변수 관리
            ├── requirements.txt  # Python 의존성 목록
            ├── pytest.ini        # pytest 비동기 설정
            ├── .env              # API 키 등 환경변수 (gitignore 대상)
            ├── .env.example      # .env 템플릿
            ├── chains/
            │   ├── prompt_templates.py  # ■Router: ROUTER_SYSTEM_PROMPT, build_router_prompt()
            │   │                        # □Worker: MODE1~8_SYSTEM, build_worker_prompt() 작성 예정
            │   └── health_chain.py      # ■Router: _run_router, 백엔드 페치, run_chat_chain
            │                            # □Worker: _call_worker_ai 등 stub → 팀원 구현 예정
            ├── models/
            │   ├── request_models.py    # AIChatRequest, MealRequest, RecommendRequest
            │   └── response_models.py   # AIChatResponse, MealResponse, RecommendResponse, RouterResult
            ├── routers/
            │   ├── generate.py          # POST /ai-chat, /process-meal, /recommend
            │   └── health.py            # GET /health
            └── utils/
                └── output_parser.py     # 레거시 (현재 미사용)
```

---

## 핵심 아키텍처: Router-Worker 두 트랙 파이프라인

```
WAS 요청
    │
    ├─── POST /process-meal ──→ [□Worker AI 담당] _call_meal_worker_ai()
    │      (Router AI 바이패스)
    │
    ├─── POST /recommend ─────→ [□Worker AI 담당] _call_recommend_worker_ai()
    │      (AI 전체 바이패스)
    │
    └─── POST /ai-chat
              │
              ▼
         [■Router AI 담당] _run_router()
         LangChain Structured Output → RouterResult { selected_mode, reason }
              │ mode 1~6
              ├─ Mode 3 → [■Router AI] _fetch_current_exercise_list() [TODO: 실제 API 연동]
              ├─ Mode 5 → [■Router AI] _fetch_current_diet_list()     [TODO: 실제 API 연동]
              │
              ▼
         [□Worker AI 담당] _call_worker_ai(mode, router_result, request, user_vars, extra_context)
         현재 stub — 팀원이 Worker AI 프롬프트 + Gemini 호출 로직 구현 예정
```

### 모드 분류 체계

| 모드 | 설명 | 엔드포인트 | Router AI | extra_context |
|:---:|---|---|:---:|---|
| 1 | 단순 대화/질문 | `/ai-chat` | ✅ | - |
| 2 | 운동 플랜 작성 | `/ai-chat` | ✅ | - |
| 3 | 운동 플랜 수정 | `/ai-chat` | ✅ | 현재 운동 목록 (백엔드 페치) |
| 4 | 식단 플랜 작성 | `/ai-chat` | ✅ | - |
| 5 | 식단 플랜 수정 | `/ai-chat` | ✅ | 현재 식단 목록 (백엔드 페치) |
| 6 | 사용자 정보 수정 | `/ai-chat` | ✅ | - |
| 7 | 식단 기록 | `/process-meal` | 바이패스 | - |
| 8 | 운동·식단 추천 | `/recommend` | 바이패스 | - |

---

## 주요 파일별 역할

### `chains/prompt_templates.py`

**■ Router AI 담당 (완료)**
- `ROUTER_SYSTEM_PROMPT`: 모드 1~6 분류 시스템 프롬프트
  - Few-shot 예시 21개, 모드 간 혼동 방지 규칙 포함
  - Input variable: `{current_message}`
- `build_router_prompt() → ChatPromptTemplate`: Router AI 프롬프트 템플릿 반환

**□ Worker AI 담당 (팀원 작성 예정)**
- `MODE1_SYSTEM` ~ `MODE8_SYSTEM`: 모드별 시스템 프롬프트
- `build_worker_prompt(mode: int) → ChatPromptTemplate`: 모드별 Worker AI 프롬프트 반환
  - 필요한 input variables:
    - 공통: `{gender}`, `{age}`, `{bmi}`, `{goal}`, `{activity_level}`, `{medical_history}`, `{allergies}`
    - 공통: `{chat_history}` (MessagesPlaceholder), `{user_instructions_block}`, `{current_message}`
    - 모드 1~5만: `{router_context}` (Router AI 결과값)
    - 모드 3만: `{current_exercise_list_block}`
    - 모드 5만: `{current_diet_list_block}`

### `chains/health_chain.py`

**■ Router AI 담당 (완료)**

| 함수 | 역할 |
|---|---|
| `_run_router(llm, message) → RouterResult` | LangChain Structured Output으로 모드 1~6 분류 |
| `_fetch_current_exercise_list(user_id)` | [더미] 백엔드 운동 계획 조회 (Mode 3용) |
| `_fetch_current_diet_list(user_id)` | [더미] 백엔드 식단 조회 (Mode 5용) |
| `_format_exercise_list_block(list)` | 운동 목록 → 프롬프트 삽입용 텍스트 변환 |
| `_format_diet_list_block(list)` | 식단 목록 → 프롬프트 삽입용 텍스트 변환 |
| `_build_user_vars(profile)` | UserProfile → 프롬프트 변수 dict 변환 |
| `run_chat_chain(request)` | Router AI 실행 → Worker AI 인터페이스 호출 |
| `run_meal_chain(request)` | Router AI 바이패스 → Worker AI 인터페이스 호출 |
| `run_recommend_chain(request)` | Router AI + Worker AI 바이패스 → 인터페이스 호출 |

**□ Worker AI 담당 (stub 상태 — 팀원 구현 예정)**

| 함수 | 반환 형식 |
|---|---|
| `_call_worker_ai(mode, router_result, request, user_vars, extra_context)` | `AIChatResponse` dict |
| `_call_meal_worker_ai(request, user_vars)` | `MealResponse` dict |
| `_call_recommend_worker_ai(request, user_vars)` | `RecommendResponse` dict |

### `models/request_models.py`

```python
class BaseUserProfile:  gender, age, bmi, goal
class ChatUserProfile(BaseUserProfile)          # POST /ai-chat용
class MealUserProfile(BaseUserProfile)          # + medical_history, allergies
class RecommendUserProfile(BaseUserProfile)     # + activity_level

class AIChatRequest:    user_id, user_profile: ChatUserProfile, user_instruction, user_message
class MealRequest:      user_id, user_profile: MealUserProfile, user_instruction, user_message
class RecommendRequest: user_id, user_profile: RecommendUserProfile, user_instruction
```

### `models/response_models.py`

```python
# Router AI 내부 전용
class RouterResult:         selected_mode (1~6), reason

# POST /ai-chat
class PlanItem:             type, detail, value          # 운동·식단 공용
class Plan:                 date, items: list[PlanItem]
class DBUpdate:             field, new_value
class ChatData:             message, plan: Plan|None, db_update: DBUpdate|None
class AIChatResponse:       status, mode, data: ChatData

# POST /process-meal
class MealData:             calories, message
class MealResponse:         status, data: MealData

# POST /recommend
class RecommendedExercise:  name, burn_calories
class RecommendedMeal:      name, calories
class RecommendData:        recommended_exercise, recommended_meal
class RecommendResponse:    status, data: RecommendData
```

---

## API 엔드포인트

### `POST /ai-chat` — 채팅 (모드 1~6)

**Request:**
```json
{
  "user_id": "user-001",
  "user_profile": { "gender": "female", "age": 28, "bmi": 22.5, "goal": "체중 감량" },
  "user_instruction": "짧게 답변해줘",
  "user_message": "1주일 운동 루틴 짜줘"
}
```

**Response (현재 — Router AI stub 상태):**
```json
{
  "status": "success",
  "mode": 2,
  "data": {
    "message": "[Worker AI 미구현] Router AI가 '운동 플랜 작성' 모드로 분류했습니다. (근거: ...)",
    "plan": null,
    "db_update": null
  }
}
```

**Response (Worker AI 완성 후 — Mode 2 예시):**
```json
{
  "status": "success",
  "mode": 2,
  "data": {
    "message": "운동 계획이 생성되었습니다.",
    "plan": {
      "date": "2026-03-21 ~ 2026-03-27",
      "items": [
        { "type": "유산소", "detail": "러닝 - 월/수/금", "value": "30분" }
      ]
    },
    "db_update": null
  }
}
```

### `POST /process-meal` — 식단 기록 (모드 7, Router AI 바이패스)

**Request:**
```json
{
  "user_id": "user-001",
  "user_profile": { "gender": "female", "age": 28, "bmi": 22.5, "goal": "체중 감량", "medical_history": [], "allergies": ["견과류"] },
  "user_message": "점심에 닭가슴살 샐러드 먹었어"
}
```

### `POST /recommend` — 운동·식단 추천 (모드 8, AI 바이패스)

**Request:**
```json
{
  "user_id": "user-001",
  "user_profile": { "gender": "male", "age": 30, "bmi": 25.1, "goal": "체중 감량", "activity_level": "보통" }
}
```

### `GET /health`
서버 상태 확인. `{ "status": "ok", "service": "ai-core" }` 반환.

---

## 로컬 실행 방법

```powershell
cd develop/ai-model/ai_core

# 가상환경 생성 및 활성화
python -m venv venv
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; .\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# .env 설정 (GOOGLE_API_KEY 필수)
Copy-Item .env.example .env
# .env 파일에서 GOOGLE_API_KEY=실제_키 입력

# 서버 실행
uvicorn main:app --port 8000

# Swagger UI: http://localhost:8000/docs
```

---

## 환경 변수 (.env)

| 키 | 설명 | 기본값 |
|---|---|---|
| `GOOGLE_API_KEY` | Google Gemini API 키 (필수) | - |
| `GEMINI_MODEL` | 사용할 Gemini 모델 | `gemini-2.0-flash` |
| `APP_ENV` | 실행 환경 | `development` |
| `APP_PORT` | 서버 포트 | `8000` |
| `CORS_ORIGINS` | CORS 허용 오리진 (쉼표 구분) | `http://localhost:3000` |

> `.env` 파일은 `.gitignore`에 포함되어 있어 API 키가 Git에 노출되지 않습니다.

---

## 기술 스택

| 카테고리 | 기술 |
|---|---|
| 웹 프레임워크 | FastAPI |
| AI/LLM | LangChain + Google Gemini (`gemini-2.0-flash`) |
| Structured Output | `llm.with_structured_output(RouterResult)` — Router AI 전용 |
| 데이터 검증 | Pydantic v2 |
| 설정 관리 | pydantic-settings + python-dotenv |
| 서버 | uvicorn |

---

## 설계 원칙 및 주의사항

1. **Router AI Structured Output**: `with_structured_output(RouterResult)`로 `{selected_mode, reason}` JSON을 강제. LLM이 잘못된 형식을 반환하면 LangChain이 자동 재시도.
2. **Router AI 결과값 전달**: 모드 1~5의 Worker AI는 `router_result`(선택 모드 + 근거)를 추가 컨텍스트로 받음. 모드 6은 공통값만 사용 (스펙 기준).
3. **모드 3/5 백엔드 페치**: Router AI가 모드를 분류한 직후, FastAPI가 백엔드에 현재 운동/식단 목록을 요청하여 Worker AI에 전달.
4. **사용자 정보 은닉**: AI가 BMI·목표 등을 내부적으로 참고하되, 답변 텍스트에서 수치를 직접 언급 금지.
5. **Fallback 안전장치**: 각 chain 함수에 `try/except`로 `CHAT_FALLBACK`, `MEAL_FALLBACK`, `RECOMMEND_FALLBACK` 보장.
6. **Python 3.9 호환**: `str | None` 대신 `Optional[str]` 사용.

---

## 미구현 / 향후 과제

**Worker AI 팀 담당:**
- [ ] `_call_worker_ai()` — 모드 1~6 Worker AI 프롬프트 + Gemini 호출 + 응답 파싱
- [ ] `_call_meal_worker_ai()` — 식단 기록 칼로리 분석 (Mode 7)
- [ ] `_call_recommend_worker_ai()` — 운동·식단 추천 알고리즘 (Mode 8)
- [ ] `build_worker_prompt(mode)` — 모드별 Worker AI 프롬프트 템플릿

**공통 / Router AI 팀 담당:**
- [ ] `_fetch_current_exercise_list()` — 실제 백엔드 API 호출로 교체 (Mode 3)
- [ ] `_fetch_current_diet_list()` — 실제 백엔드 API 호출로 교체 (Mode 5)
- [ ] Vector DB 연동 — 대화 이력 저장·조회
- [ ] 백엔드(Node.js/Spring Boot) 연동 E2E 테스트
