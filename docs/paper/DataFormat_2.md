# [Specification] 추천 항목 확정(좋아요) API 명세 (sequence_2)

이 문서는 사용자가 추천받은 항목을 '좋아요(추택)'하여 자신의 캘린더에 확정 등록하는 프로세스에 대한 규격을 정의합니다.
이 과정은 **AI(FastAPI)가 개입하지 않는** 순수 비즈니스 로직입니다.

## 1. 추천 항목 확정 (Confirmation)

### 1.1 Front → WAS 요청 (POST /confirm-recommendation)
사용자가 선택한 추천 항목 정보를 서버에 저장 요청합니다.

```json
{
  "user_id": "string",
  "item_type": "string",       // "exercise" 또는 "meal"
  "item_id": "string",         // 추천된 항목의 고유 ID (있을 경우)
  "item_details": {
    "name": "string",          // 운동/식단 이름
    "calories": "number",      // (운동 시 소모 / 식단 시 섭취) 칼로리
    "date": "YYYY-MM-DD",      // 등록할 날짜
    "time_slot": "string",     // (식단 시) 아침, 점심, 저녁 등 (운동일 경우 null/생략 가능)
    "sets_reps": "string"      // (운동 시) 3세트 15회 등 (식단일 경우 null/생략 가능)
  }
}
```

### 1.2 WAS → Front 응답
성공적으로 DB에 저장되었음을 알립니다.

```json
{
  "status": "success",
  "message": "성공적으로 저장되었습니다.",
  "data": {
    "entry_id": "string"       // DB에 생성된 고유 기록 ID
  }
}
```

---

## 2. 데이터베이스 처리 (WAS Internal)
- **FastAPI 호출 없음**: AI 분석 단계가 아니므로 WAS에서 직접 DB 작업을 수행합니다.
- **DB 테이블**: 사용자의 `user_daily_plans` 또는 `user_meal_logs` 테이블에 데이터를 추가합니다.
- **성공 후 처리**: 프론트엔드에서는 응답을 받은 후 즉시 사용자 **캘린더**에 해당 항목을 자동으로 렌더링하고 사용자에게 알림을 표시합니다.
