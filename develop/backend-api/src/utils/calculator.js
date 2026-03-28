/**
 * 목표 칼로리 및 단탄지 계산 알고리즘
 * 참고 공식: Mifflin-St Jeor Equation
 * 
 * @param {string} gender 'male' | 'female'
 * @param {number} age
 * @param {number} height cm
 * @param {number} weight kg
 * @param {string} activityLevel 활동 레벨 (예: 'sedentary', 'light', 'moderate', 'active', 'very_active')
 * @param {string} goal 건강 목적 (예: 'weight_loss', 'maintain', 'muscle_gain')
 * @returns {object} { target_calories, target_carbs, target_protein, target_fat }
 */
exports.calculateTargets = (gender, age, height, weight, activityLevel, goal) => {
  if (!age || !height || !weight) return null;

  // 1. 기초대사량(BMR) 계산 (Mifflin-St Jeor)
  let bmr = 10 * weight + 6.25 * height - 5 * age;

  // 성별은 'male' 또는 'female'로만 입력됨
  const isMale = gender === 'male';
  bmr = isMale ? bmr + 5 : bmr - 161;

  // 2. 활동 계수 (Activity factor)
  // 프론트엔드 입력값 기준
  const activityFactors = {
    '거의 없음': 1.2,
    '가벼운 활동': 1.375,
    '보통': 1.55,
    '격렬한 운동': 1.725
  };

  const factor = activityFactors[activityLevel] || 1.2; // 매칭 실패 시 기본값 1.2

  const tdee = bmr * factor;

  // 3. 목표 조정 칼로리
  let targetCalories = tdee;
  let ratio = { carbs: 0.5, protein: 0.3, fat: 0.2 }; // 기본값 (건강 유지)

  if (goal === '다이어트') {
    targetCalories = tdee - 500;
    ratio = { carbs: 0.4, protein: 0.4, fat: 0.2 };
  } else if (goal === '근력 향상') {
    targetCalories = tdee + 500;
    ratio = { carbs: 0.4, protein: 0.3, fat: 0.3 };
  } else if (goal === '건강 유지') {
    targetCalories = tdee;
    ratio = { carbs: 0.5, protein: 0.3, fat: 0.2 };
  }

  // 예외 방지: 기초 대사량 이하로 떨어지지 않도록 하한선 설정
  const minCalories = isMale ? 1500 : 1200;
  if (targetCalories < minCalories) targetCalories = minCalories;

  targetCalories = Math.round(targetCalories);

  // 4. 단탄지 그램(g) 비율에 맞춰 계산
  // 탄수화물(4kcal/g), 단백질(4kcal/g), 지방(9kcal/g)
  const targetCarbs = Math.round((targetCalories * ratio.carbs) / 4);
  const targetProtein = Math.round((targetCalories * ratio.protein) / 4);
  const targetFat = Math.round((targetCalories * ratio.fat) / 9);

  return {
    target_calories: targetCalories,
    target_carbs: targetCarbs,
    target_protein: targetProtein,
    target_fat: targetFat
  };
};
