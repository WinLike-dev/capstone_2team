const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const auth = require('../middleware/authMiddleware');

// 모든 user 라우트에 JWT 인증 미들웨어 적용
router.use(auth);

// 기본 유저 정보
router.get('/me', userController.getMe);

// 1. 건강 프로필 (user_health_profiles)
router.get('/profile', userController.getProfile);
router.post('/profile', userController.saveProfile);

// 2. 운동 플랜 (user_exercise_plans)
router.get('/exercises', userController.getExercises);
router.post('/exercises', userController.addExercise);
router.put('/exercises/:id', userController.updateExercise);
router.delete('/exercises/:id', userController.deleteExercise);

// 3. 식단 플랜 (user_meal_plans)
router.get('/meals', userController.getMeals);
router.post('/meals', userController.addMeal);
router.delete('/meals/:id', userController.deleteMeal);

module.exports = router;
