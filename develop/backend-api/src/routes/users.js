const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const authMiddleware = require('../middleware/auth');

// 모든 users 관련 API에 JWT 토큰 인증 강제 적용
router.use(authMiddleware);

// 1. 건강 프로필 (user_health_profiles)
router.get('/profile', userController.getProfile);
router.post('/profile', userController.saveProfile);

// 1-1. 캘린더 통합 조회 (user_exercise_plans, user_meal_plans)
router.get('/calendar', userController.getCalendar);

// 2. 운동 플랜 (user_exercise_plans, exercise_items)
router.put('/exercises/items/:item_id', userController.updateExerciseItem);

// 3. 식단 플랜 (user_meal_plans)
router.put('/meals/:id', userController.updateMealStatus);

// 4. 홈 추천 다이렉트 추가 및 교체
router.post('/exercises/recommend-add', userController.addRecommendedExercise);
router.put('/meals/recommend-replace', userController.replaceRecommendedMeal);

module.exports = router;
