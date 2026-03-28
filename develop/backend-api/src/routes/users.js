const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');

// 기본 유저 정보 (프로토타입: 인증 미들웨어 없음, 추후 추가 예정)
// router.get('/me', userController.getMe);

// 1. 건강 프로필 (user_health_profiles)
router.get('/profile', userController.getProfile);
router.post('/profile', userController.saveProfile);
router.put('/profile', userController.updateProfile);
router.put('/targets', userController.updateTargets);

// 2. 운동 플랜 (user_exercise_plans, exercise_items)
router.get('/exercises', userController.getExercises);
router.post('/exercises', userController.addExercise);
router.put('/exercises/items/:item_id', userController.updateExerciseItem);
router.delete('/exercises/:id', userController.deleteExercise);

// 3. 식단 플랜 (user_meal_plans)
router.get('/meals', userController.getMeals);
router.post('/meals', userController.addMeal);
router.delete('/meals/:id', userController.deleteMeal);

// 4. 추천 항목 확정 (DataFormat_2)
router.post('/confirm-recommendation', userController.confirmRecommendation);

module.exports = router;
