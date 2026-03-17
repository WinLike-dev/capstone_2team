const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const auth = require('../middleware/authMiddleware');

// 모든 user 라우트에 JWT 인증 미들웨어 적용
router.use(auth);

// /api/v1/users 라우트 정의
router.get('/me', userController.getMe);
router.put('/me', userController.updateMe);
router.get('/me/health', userController.getHealthData);
router.post('/me/health', userController.saveHealthData);

module.exports = router;
