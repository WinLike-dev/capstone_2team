const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const auth = require('../middleware/authMiddleware');

// 모든 user 라우트에 JWT 인증 미들웨어 적용
router.use(auth);

// 기본 유저 정보
router.get('/me', userController.getMe);

// 1. 온보딩 / 프로필 정보
router.get('/profile', userController.getProfile);
router.post('/profile', userController.saveProfile);

// 2. 대시보드 통계 (걸음수, 칼로리 등)
router.get('/dashboard', userController.getDashboard);
router.post('/dashboard', userController.saveDashboard);

// 3. 할 일 (Todos)
router.get('/todos', userController.getTodos);
router.post('/todos', userController.addTodo);
router.put('/todos/:id', userController.updateTodo);
router.delete('/todos/:id', userController.deleteTodo);

module.exports = router;
