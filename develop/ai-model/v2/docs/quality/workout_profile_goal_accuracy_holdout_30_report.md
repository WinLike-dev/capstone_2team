# Workout Profile Goal Accuracy Holdout 30 Report

- Runner: `test_workout_profile_goal_accuracy_holdout_30_suite.py`
- Profile data: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\data\workout_profile_goal_holdout_profiles_30.json`
- Cases: 30
- Overall average: 1.0
- Pass/Review/Fail: 30/0/0
- Goal distribution: `{"fat_loss": 9, "muscle_gain": 8, "mobility": 9, "consistency": 4}`
- Orientation distribution: `{"introvert": 15, "extrovert": 15}`

## Criterion Pass Rate

- constraint_fit: 1
- four_category_coverage: 1
- goal_marker_fit: 1
- goal_priority: 1
- level_time_frequency_fit: 1
- profile_signal_fit: 1
- routed_to_workout_plan: 1
- safety_fit: 1
- social_orientation_fit: 1

## Case Details

### h01 / pass (1.0)
- Profile: 24세, female, 70kg, beginner, fat_loss, 내향형, 주 2회, 12분
- Expected: orientation=introvert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h02 / pass (1.0)
- Profile: 35세, male, 88kg, intermediate, fat_loss, 외향형, 주 4회, 30분
- Expected: orientation=extrovert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h03 / pass (1.0)
- Profile: 29세, male, 74kg, advanced, muscle_gain, introvert, 주 5회, 50분
- Expected: orientation=introvert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h04 / pass (1.0)
- Profile: 43세, female, 67kg, advanced, strength, extroverted, 주 5회, 45분
- Expected: orientation=extrovert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h05 / pass (1.0)
- Profile: 68세, female, 61kg, beginner, mobility, 내향형, 주 3회, 15분
- Expected: orientation=introvert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h06 / pass (1.0)
- Profile: 55세, male, 90kg, beginner, health, 외향형, 주 3회, 20분
- Expected: orientation=extrovert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h07 / pass (1.0)
- Profile: 31세, nonbinary, 64kg, beginner, consistency, 혼자 운동 선호, 주 2회, 10분
- Expected: orientation=introvert, goal=consistency, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 2, "하체": 3}`

### h08 / pass (1.0)
- Profile: 26세, female, 59kg, intermediate, habit, group workout, 주 3회, 25분
- Expected: orientation=extrovert, goal=consistency, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 2, "하체": 3}`

### h09 / pass (1.0)
- Profile: 47세, male, 95kg, beginner, weight_loss, I, 주 3회, 18분
- Expected: orientation=introvert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h10 / pass (1.0)
- Profile: 39세, female, 80kg, intermediate, fat_loss, E, 주 4회, 25분
- Expected: orientation=extrovert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h11 / pass (1.0)
- Profile: 34세, male, 72kg, intermediate, muscle_gain, quiet solo routine, 주 4회, 35분
- Expected: orientation=introvert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h12 / pass (1.0)
- Profile: 30세, female, 58kg, advanced, strength, social, 주 5회, 40분
- Expected: orientation=extrovert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h13 / pass (1.0)
- Profile: 50세, female, 66kg, beginner, health, 내향형, 주 3회, 15분
- Expected: orientation=introvert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h14 / pass (1.0)
- Profile: 72세, male, 70kg, beginner, mobility, 외향형, 주 2회, 12분
- Expected: orientation=extrovert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h15 / pass (1.0)
- Profile: 22세, female, 49kg, beginner, fat_loss, introverted, 주 3회, 20분
- Expected: orientation=introvert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h16 / pass (1.0)
- Profile: 44세, male, 103kg, advanced, fat_loss, 외향형, 주 5회, 35분
- Expected: orientation=extrovert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h17 / pass (1.0)
- Profile: 27세, female, 55kg, beginner, muscle_gain, 내향형, 주 3회, 25분
- Expected: orientation=introvert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h18 / pass (1.0)
- Profile: 33세, male, 78kg, beginner, strength, 외향형, 주 2회, 20분
- Expected: orientation=extrovert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h19 / pass (1.0)
- Profile: 52세, female, 84kg, beginner, glucose_control, introvert, 주 4회, 20분
- Expected: orientation=introvert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h20 / pass (1.0)
- Profile: 60세, male, 82kg, beginner, heart_health, extrovert, 주 3회, 15분
- Expected: orientation=extrovert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h21 / pass (1.0)
- Profile: 45세, female, 89kg, beginner, habit, 혼자 조용히, 주 2회, 8분
- Expected: orientation=introvert, goal=consistency, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 2, "하체": 3}`

### h22 / pass (1.0)
- Profile: 38세, male, 76kg, intermediate, consistency, 함께 운동 선호, 주 3회, 20분
- Expected: orientation=extrovert, goal=consistency, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 2, "하체": 3}`

### h23 / pass (1.0)
- Profile: 36세, female, 77kg, intermediate, fat_loss, solo home workout, 주 4회, 25분
- Expected: orientation=introvert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h24 / pass (1.0)
- Profile: 66세, female, 87kg, beginner, weight_loss, 외향형, 주 3회, 20분
- Expected: orientation=extrovert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h25 / pass (1.0)
- Profile: 40세, male, 69kg, intermediate, mobility, introvert, 주 4회, 30분
- Expected: orientation=introvert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h26 / pass (1.0)
- Profile: 25세, female, 60kg, intermediate, health, extrovert, 주 4회, 35분
- Expected: orientation=extrovert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`

### h27 / pass (1.0)
- Profile: 65세, male, 71kg, advanced, muscle_gain, 내향형, 주 3회, 20분
- Expected: orientation=introvert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h28 / pass (1.0)
- Profile: 23세, female, 63kg, advanced, strength, 외향형, 주 6회, 60분
- Expected: orientation=extrovert, goal=muscle_gain, first=upper_body
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 2, "상체": 0, "하체": 1}`

### h29 / pass (1.0)
- Profile: 34세, female, 82kg, beginner, diet, 내향형, 주 2회, 10분
- Expected: orientation=introvert, goal=fat_loss, first=cardio
- Failed checks: none
- Category positions: `{"스트레칭": 3, "유산소": 0, "상체": 2, "하체": 1}`

### h30 / pass (1.0)
- Profile: 70세, female, 65kg, beginner, health, 외향형, 주 2회, 10분
- Expected: orientation=extrovert, goal=mobility, first=stretching
- Failed checks: none
- Category positions: `{"스트레칭": 0, "유산소": 1, "상체": 3, "하체": 2}`
