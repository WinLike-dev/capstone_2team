# [Specification] 사용자 건강 정보 및 성향 API 명세 (sequence_1)

이 문서는 사용자의 MBTI 및 상세 건강 정보를 서버(WAS)에 저장하기 위한 API 및 DB 규격을 정의합니다.

## 1. JSON 요청 규격 (Request Payload)
클라이언트(Front-end)에서 서버(WAS)로 데이터를 전송할 때 사용하는 모델입니다.

```json
{
  "user_id": "string",          // 사용자 식별자 (Unique ID)
  "mbti": "string",             // MBTI 유형 (예: "INTJ")
  "gender": "string",           // 성별 ("male", "female")
  "age": "number",              // 나이
  "height": "number",           // 키 (cm) - BMI 계산 참고용
  "weight": "number",           // 몸무게 (kg) - BMI 계산 참고용
  "bmi": "number",              // [신규] 비만수치 (WAS에서 계산하여 반환)
  "goal": "string",             // 건강/운동 목표 (예: "다이어트", "근력 향상", "건강 유지")
  "activity_level": "string",   // 평소 활동량 (예: "거의 없음", "가벼운 활동", "보통", "격렬한 활동")
  "medical_history": ["string"], // 기저질환 목록 (배열 형태)
  "allergies": ["string"],       // 알러지 목록 (배열 형태)
  "user_instruction": "string",  // 사용자 지시사항 및 특이사항 (설명글)
  "target_calories": "number",   // 하루 목표 섭취 칼로리
  "target_carbs": "number",      // 하루 목표 탄수화물 (g)
  "target_protein": "number",    // 하루 목표 단백질 (g)
  "target_fat": "number"         // 하루 목표 지방 (g)
}
```

> [!WARNING]
> **BMI 계산 지침**
> - 서버(WAS)가 BMI를 계산하여 응답으로 내려줍니다.
> - **Front-end**는 직접 공식을 사용하지 않으며, 서버의 응답 값을 저장 및 노출하는 역할만 수행합니다.

---

## 2. 데이터베이스 스키마 (DB Schema)
사용자 상세 건강 정보를 저장하기 위한 테이블 구조입니다.

### **Table: user_health_profiles**
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| **user_id** | VARCHAR(50) | PRIMARY KEY, FK | 사용자 계정 고유 ID |
| **mbti** | CHAR(4) | NULLABLE | MBTI 유형 (4자) |
| **gender** | VARCHAR(10) | NOT NULL | 성별 |
| **age** | INTEGER | NOT NULL | 나이 |
| **bmi** | DECIMAL(4,1) | NOT NULL | **[Backend 계산값]** 비만수치 |
| **goal** | VARCHAR(100) | NULLABLE | 건강 관리 목적 |
| **activity_level** | VARCHAR(50) | NULLABLE | 평소 활동량 |
| **medical_history** | TEXT | NULLABLE | 기저질환 정보 (목록) |
| **allergies** | TEXT | NULLABLE | 알러지 정보 (목록) |
| **user_instruction** | TEXT | NULLABLE | **사용자 지시사항 (문자열)** |
| **target_calories** | INTEGER | DEFAULT 2000 | 하루 목표 섭취 칼로리 |
| **target_carbs** | INTEGER | DEFAULT 250 | 목표 탄수화물 (g) |
| **target_protein** | INTEGER | DEFAULT 80 | 목표 단백질 (g) |
| **target_fat** | INTEGER | DEFAULT 50 | 목표 지방 (g) |
| **updated_at** | TIMESTAMP | DEFAULT NOW() | 최신 수정 시각 |

---

### 3. 처리 흐름 (Sequence)
1. 사용자가 Front에서 건강 정보를 입력합니다.
2. Front에서 키, 몸무게를 입력해 저장하면 **WAS가 BMI를 계산해 응답**합니다.
3. `/api/user/profile` 엔드포인트로 JSON 데이터를 전송합니다.
4. **WAS(Node.js)**는 **FastAPI 호출 없이** 직접 DB(`user_health_profiles`)를 업데이트합니다.
5. 성공 시 사용자에게 저장 완료 알림을 표시합니다.
