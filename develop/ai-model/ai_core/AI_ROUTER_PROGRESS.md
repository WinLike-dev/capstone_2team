# AI Core 마이크로서비스 진행 상태

> 마지막 업데이트: 2026-03-16

---

## 📌 프로젝트 개요

**FastAPI + LangChain(Gemini Flash)** 기반 헬스케어 앱의 AI Core 마이크로서비스.
백엔드와 메인 AI 모델 사이에 **AI 라우터(Router)** 로직을 추가하여, 사용자 발화를 먼저 분류한 뒤 인텐트에 맞는 AI 응답을 생성하는 2단계 파이프라인을 구현.

---

## ✅ 구현 완료 사항

### 1. AI 라우터 핵심 로직 (`chains/health_chain.py`)

2단계 LCEL 파이프라인:

1. **인텐트 분류기** (`_classify_intent`)
   - 사용자 발화 → Gemini에 전달 → 1~4 숫자 반환
   - 같은 API 키 사용, 토큰 소비 최소화

2. **메인 응답 생성기** (`_generate_main_response`)
   - 분류된 인텐트에 따라 적합한 시스템 프롬프트 선택
   - `UserContext`를 결합하여 개인화된 평문 응답 생성

3. **응답 래핑** (`wrap_plain_text_response`)
   - 평문 → `GenerateResponse` JSON 포맷으로 변환
   - 인텐트에 따라 `action_type` 및 `ui_components` 동적 매핑

---

### 2. 인텐트 분류 시스템 (`chains/prompt_templates.py`)

| 인텐트 | 설명 | action_type | widget |
|:---:|---|---|---|
| **1** | 단순 질문 (건강/운동/식단 일반 지식) | `advice` | `null` |
| **2** | 계획 추가/수정 (운동 플랜 변경) | `ui_update` | `plan_editor` |
| **3** | 사용자 정보 수정 (체중/키 등 DB 변경) | `ui_update` | `profile_editor` |
| **4** | 식단 구성 (하루/주간 식단 구성 요청) | `ui_update` | `diet_planner` |

**오분류 방지:** 1번(단순 질문)과 4번(식단 구성)을 혼동하지 않도록 분류 기준 및 8가지 예시를 분류기 프롬프트에 명시.

---

### 3. 사용자 컨텍스트 (`models/request_models.py`)

```python
class UserContext(BaseModel):
    age: Optional[int]      # 나이
    gender: Optional[str]   # 성별
    height: Optional[float] # 키 (cm)
    weight: Optional[float] # 체중 (kg)
    mbti: Optional[str]     # MBTI 유형
    # weather_condition 제거됨
```

- 키·체중은 AI가 내부적으로 적정 칼로리·운동 강도 계산에 활용
- MBTI는 동기부여 방식·식단 접근법 조정에 활용
- **답변 텍스트에서 사용자 정보를 직접 언급하지 않음** (자연스러운 응답)

---

### 4. 응답 규칙 (프롬프트 공통 지침)

| 인텐트 | 답변 길이 제한 |
|:---:|---|
| 1 (단순 질문) | 3~4문장 이내 |
| 2 (계획 수정) | 3~4문장 이내 |
| 3 (DB 수정) | 2~3문장 이내 |
| 4 (식단 구성) | 5문장 이내 (아침/점심/저녁 한 줄씩) |

---

### 5. 테스트 (`tests/test_api.py`)

- **11/11 pytest PASS** ✅
- `_classify_intent` / `_generate_main_response` 함수 레벨 AsyncMock 패치 방식 사용
- 커버리지: 헬스체크, 인텐트 1~4 케이스, 대화 이력 포함 케이스, 422 유효성 검사, output_parser 단위 테스트

---

## 📁 수정된 파일 목록

```
ai_core/
├── models/
│   └── request_models.py       # UserContext: height, weight, mbti 추가 / weather 제거
├── chains/
│   ├── prompt_templates.py     # 분류기 + 4가지 인텐트별 시스템 프롬프트
│   └── health_chain.py         # 2단계 LCEL 파이프라인 구현
├── utils/
│   └── output_parser.py        # wrap_plain_text_response, parse_intent
├── routers/
│   └── generate.py             # API 엔드포인트 (변경 최소)
└── tests/
    └── test_api.py             # 11개 테스트 케이스
```

---

## 🚀 로컬 실행 방법

```powershell
# 서버 시작
.\venv\Scripts\uvicorn.exe main:app --port 8000

# Swagger UI
http://localhost:8000/docs

# 테스트 실행
.\venv\Scripts\pytest.exe tests/ -v
```

---

## 🔑 환경 변수 (`.env`)

```
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

> `.env` 파일은 `.gitignore`에 포함되어 있어 API 키가 외부에 노출되지 않습니다.

---

## 📨 API 요청/응답 예시

### 요청 포맷
```json
{
  "user_id": "user-001",
  "user_context": {
    "age": 28,
    "gender": "female",
    "height": 162.0,
    "weight": 55.0,
    "mbti": "ENFP"
  },
  "chat_history": [],
  "current_message": "소화에 좋은 음식 추천해줘"
}
```

### 응답 포맷 (인텐트별)

| 케이스 | 발화 예시 | 응답 widget |
|---|---|---|
| 1. 단순 질문 | "소화에 좋은 음식 추천해줘" | `null` |
| 2. 계획 수정 | "운동 루틴 바꿔줘" | `plan_editor` |
| 3. 정보 수정 | "체중이 50kg으로 줄었어" | `profile_editor` |
| 4. 식단 구성 | "오늘 식단 짜줘" | `diet_planner` |

---

## 🔜 다음 단계 (미구현)

- [ ] 백엔드 연동 테스트 (실제 UserContext 데이터 흐름 확인)
- [ ] 프론트엔드 위젯 연동 (`plan_editor`, `diet_planner`, `profile_editor`)
- [ ] 대화 이력(chat_history) 기반 맥락 유지 검증
- [ ] 실제 사용자 발화 기반 인텐트 분류 정확도 검토
