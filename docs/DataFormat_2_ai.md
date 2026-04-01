# Sequence_3: AI 채팅 (단순대화, 플랜/식단 추천/수정, DB 수정)

이 문서는 사용자와 AI 간의 채팅 인터랙션 및 내부 라우팅, 데이터 연동 프로세스를 정의합니다.

## 1. 시퀀스 다이어그램 (Sequence Diagram)

![Sequence_ai 다이어그램](sequence_ai.png)

---

## 2. 주요 프로세스 상세

### 2.1 AI 채팅 및 의도 분류 (Router & Vector DB)
1. **[Production] 사용자 → Front → WAS**: 사용자가 채팅을 입력하면 WAS를 거쳐 AI(FastAPI)로 전달됩니다. (**POST /ai-chat**)
2. **AI (Parallel Request)**:
    - **Router AI**: 라우터 시스템 지침서와 사용자 메시지를 대조하여 6가지 모드 중 하나로 의도를 분류합니다.
    - **Vector DB**: `user_id`와 사용자 메시지를 바탕으로 이전 대화 기록 및 컨텍스트를 검색합니다.
3. **조건부 정보 조회 (수정 요청 시)**: 라우터 분류 결과가 '플랜 수정(Mode 3)' 또는 '식단 수정(Mode 5)'일 경우, FastAPI는 직접 **WAS에 현재 리스트**를 요청하여 확보합니다.
    - **Mode 3**: `GET /api/exercise-list/{user_id}` 호출
    - **Mode 5**: `GET /api/meal-list/{user_id}` 호출

### 2.2 답변 생성 및 비동기 요약 저장
- **LLM (Gemini Flash) 호출**: 
    - 입력: `사용자 메시지 + 시스템 지시사항 + 사용자 정보 + 이전 대화 기록 + 라우터 결과값 [+ 현재 리스트(수정 시)]`
    - 출력: 각 모드별 정형화된 JSON 데이터
- **결과 반환 (Response Handling)**:
    - **모든 모드**: 생성된 모든 데이터(메시지 + 추천/수정 상세 정보)를 프론트로 전달합니다.
- **Background Sync**: 답변 전송 후 비동기로 Gemini를 통해 문답을 요약하여 다음 대화를 위해 Vector DB에 저장합니다.

---

## 3. AI API 명세 (JSON 규격)

### 3.1 [Production] WAS → FastAPI 요청 (POST /ai-chat)
요청 시 사용자의 건강 프로필과 지시사항, 메시지를 포함합니다.
```json
{
  "user_id": "string",
  "user_profile": {
    "gender": "string",
    "age": "number",
    "bmi": "number",
    "goal": "string"
  },
  "user_message": "string"      // 사용자가 입력한 채팅 메시지
}
```

### 3.2 AI → WAS 응답 (모드별 상세)
Gemini Flash가 생성한 데이터가 `mode`에 따라 다르게 반환됩니다.

```json
{
  "status": "success",
  "mode": "number", // 1(단순대화), 2(플랜작성), 3(플랜수정), 4(식단작성), 5(식단수정)
  "data": {
    "message": "string",       // 사용자에게 보여줄 피드백 메시지
    "plan": {                  // 모드 2, 3, 4, 5인 경우에만 포함
      "date": "string",
      "items": [
        {
          "type": "string",    // 운동 종류 또는 식품 종류
          "detail": "string",  // 세부 항목 또는 시간(아/점/저)
          "value": "string"    // 횟수 또는 수량
        }
      ]
    }
  }
}
```

### 4. FastAPI → WAS 요청 (GET)
플랜 또는 식단 수정 모드(Mode 3, 5) 시 AI가 최신 리스트를 기반으로 분석하기 위해 WAS에 직접 요청하는 엔드포인트입니다.

| 모드 | 경로 | 설명 |
| :--- | :--- | :--- |
| **Mode 3 (플랜 수정)** | `GET /api/exercise-list/{user_id}` | 현재 등록된 운동 플랜 리스트 조회 |
| **Mode 5 (식단 수정)** | `GET /api/meal-list/{user_id}` | 현재 등록된 식단 리스트 조회 |

---