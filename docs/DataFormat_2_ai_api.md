# [Specification] 식단 기록 및 추천 AI API 명세 (sequence_2)

이 문서는 `sequence_2_ai.png`의 비즈니스 로직에 따른 FastAPI(AI) 요청 및 응답 JSON 규격을 정의합니다.

## 1. 식단 기록 (Meal Recording)

### 1.1 WAS → AI 요청 (POST /ai/meal-record)
사용자 식별자와 식단 기록 메시지만 슬림하게 전송합니다. (나머지 건강 정보는 백엔드 내부에서 `user_id`로 DB에서 확보합니다.)

```json
{
  "user_id": "string",         // 사용자 식별자
  "user_message": "string"     // 사용자가 입력한 식단 메시지 (예: "점심에 닭가슴살 샐러드 먹었어")
}
```

### 1.2 AI → WAS 응답 (Analysis Result)
Gemini Flash 분석 결과인 칼로리와 3대 영양소, 그리고 피드백 메시지를 반환합니다.

```json
{
  "status": "success",
  "data": {                   // 또는 정상 처리 실패 시 "fallback" 객체로 내려옴
    "calories": "number",    // 분석된 총 칼로리
    "carbs": "number",       // 분석된 탄수화물 (g)
    "protein": "number",     // 분석된 단백질 (g)
    "fat": "number",         // 분석된 지방 (g)
    "message": "string"      // 사용자에게 보여줄 피드백 메시지 (한 줄로 간결히)
  }
}
```

> **유연한 응답 처리 및 홈 화면 지표 업데이트** 
> 프론트엔드는 서버 응답이 `data` 객체에 있든 `fallback` 객체에 있든 유연하게 값을 읽어옵니다. 반환된 영양소 데이터(칼로리, 탄, 단, 지)는 **홈 화면의 '오늘의 영양소' 그래프와 '섭취 칼로리' 게이지를 실시간으로 업데이트**하는 데 즉시 사용되며, 애니메이션이 실행됩니다.

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
    "target_calories": "number",
    "target_carbs": "number",
    "target_protein": "number",
    "target_fat": "number",
    "activity_level": "string"
  },
  "user_instruction": "string" // 개인화된 추천을 위한 지시사항
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
