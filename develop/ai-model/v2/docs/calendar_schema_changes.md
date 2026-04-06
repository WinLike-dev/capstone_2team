# 캘린더 연동을 위한 스키마 변경 사항

## 변경 파일 목록

- `app/schemas/llm_responses.py`
- `app/schemas/was.py`
- `app/prompts/nodes/generate/draft_plan.md`
- `app/graph/nodes/generate.py`
- `.env`

---

## 1. `llm_responses.py`

### 추가: `ExerciseItem` 모델

```python
class ExerciseItem(BaseModel):
    exercise_name: str  # 세부 운동명 (예: 스쿼트, 데드리프트)
    sets: int           # 세트 수
```

### 변경: `PlanExtractItem` 필드

| 필드 | 변경 전 | 변경 후 |
|------|---------|---------|
| `name` | `"Plan item title"` | 운동 종류 또는 식사명으로 description 구체화 |
| `detail` | `"Plan item details"` | 세션/식사 설명으로 description 구체화 |
| `day` | `"Day or schedule slot"` | `"날짜 (YYYY-MM-DD 형식)"` |
| `ex_list` | 없음 | **추가** — `list[ExerciseItem]`, workout일 때만 채움 |

---

## 2. `was.py`

### 추가: `WASExerciseItem` 모델

```python
class WASExerciseItem(BaseModel):
    exercise_name: str
    sets: int = 3
```

### 변경: `WASPlanItem`에 `ex_list` 필드 추가

```python
ex_list: list[WASExerciseItem] = []  # 기존 없음 → 추가
```

### 변경: `to_plan_create`, `to_plan_update` 변환 함수

WAS로 전송 시 `ex_list`도 함께 포함되도록 업데이트.

### 버그 수정: `WASClient` — `httpx.ConnectError` 미처리

`_get`, `_post`, `_put` 메서드에 `httpx.RequestError` 예외 처리 추가.
WAS 서버가 실행 중이 아닐 때 500 오류 대신 `ExternalServiceError`로 정상 처리됨.

```python
except httpx.RequestError as exc:
    raise ExternalServiceError(service="WAS", message=f"connection error: {exc}")
```

---

## 3. `draft_plan.md`

proposed_plan 작성 규칙 추가:

- `day` → YYYY-MM-DD 형식
- `name` → 운동 종류 (근력, 유산소 등) 또는 식사 타입 (아침, 점심 등)
- `ex_list` → workout일 때만 세부 운동 목록 채움, diet는 빈 배열

계획 생성 방침 변경:
- 기존: 정보가 부족하면 계획을 만들지 말고 추가 질문
- 변경: 운동 목표와 빈도만 있어도 바로 `proposed_plan` 작성, 부상·특수 제약이 있을 때만 추가 질문 (1개 제한)

---

## 4. `generate.py`

### 변경: 오늘 날짜 시스템 프롬프트 주입

`_build_draft_system_prompt` 함수에서 매 요청마다 오늘 날짜를 프롬프트에 포함.
LLM이 `day` 필드를 오늘 기준으로 올바르게 계산할 수 있게 됨.

```python
from datetime import date
# _build_draft_system_prompt 내부
sections.append(f"오늘 날짜: {date.today().isoformat()}")
```

---

## WAS 팀 공유 필요 사항

`POST /api/plan/create`, `PUT /api/plan/update` 요청 바디의 `items` 각 항목에
`ex_list` 필드가 추가됩니다.

```json
{
  "plan_type": "workout",
  "items": [
    {
      "name": "근력",
      "detail": "하체 위주 근력 운동",
      "day": "2026-04-09",
      "ex_list": [
        { "exercise_name": "스쿼트", "sets": 3 },
        { "exercise_name": "데드리프트", "sets": 4 }
      ]
    }
  ]
}
```

diet 계획은 `ex_list`가 빈 배열(`[]`)로 전달됩니다.
