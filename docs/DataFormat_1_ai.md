# [Specification] 식단 기록 및 추천 AI API 명세 (sequence_2)

이 문서는 `sequence_2_ai.png`의 비즈니스 로직에 따른 FastAPI(AI) 요청 및 응답 JSON 규격을 정의합니다.

## 1. 식단 기록 (Meal Recording)

### 1.1 WAS → AI 요청 (POST /process-meal)
사용자의 건강 정보, 지시사항, 그리고 기록할 메시지를 전송합니다.

```json
{
  "user_id": "string",
  "user_profile": {
    "gender": "string",
    "age": "number",
    "bmi": "number",
    "goal": "string",
    "medical_history": ["string"],
    "allergies": ["string"]
  },
  "user_message": "string"     // 사용자가 입력한 식단 메시지 (예: "점심에 닭가슴살 샐러드 먹었어")
}
```

### 1.2 AI → WAS 응답 (Analysis Result)
Gemini Flash 분석 결과인 칼로리와 메시지를 반환합니다.

```json
{
  "status": "success",
  "data": {
    "calories": "number",    // 분석된 총 칼로리
    "protein": "number",
    "carbohydrate": "number",
    "fat": "number",
    "message": "string"      // 사용자에게 보여줄 피드백 메시지 (한 줄로 간결히)
  }
}
```

---

## 2. 추천 기능 (Recommendation)
### 2.1 WAS → AI 요청 (POST /recommend)
배경 실행 또는 새로고침 시 사용자 정보를 기반으로 추천을 요청합니다.

```json
{
  "user_id": "string",
  "user_profile": {
    "gender": "string",
    "age": "number",
    "bmi": "number",
    "goal": "string",
    "activity_level": "string"
  }
}
```

### 2.2 AI → WAS 응답 (Recommendation Result)
Gemini Flash가 생성한 운동 및 식단 추천 데이터를 반환합니다.

```json
{
  "status": "success",
  "data": {
    "recommended_exercise": {
      "name": "string",      // 운동 종류
      "burn_calories": "number" // 예상 소모 칼로리
    },
    "recommended_exercise": {
      "name": "string",      // 운동 종류
      "burn_calories": "number" // 예상 소모 칼로리
    },
    "recommended_exercise": {
      "name": "string",      // 운동 종류
      "burn_calories": "number" // 예상 소모 칼로리
    },
    "recommended_meal": {
      "name": "string",      // 식단 종류
      "calories": "number"   // 식단 칼로리
    },
    "recommended_meal": {
      "name": "string",      // 식단 종류
      "calories": "number"   // 식단 칼로리
    }
  }
}
```

---

## 3. 벡터 DB 저장 (Background Sync)
AI 내부에서 Gemini를 통해 요약한 후 Vector DB에 저장되는 데이터 형식입니다.

```json
{
  "user_id": "string",
  "summary": "string",       // 대화 내용 요약본
  "timestamp": "ISO8601"
}
```
