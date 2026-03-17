const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const auth = require('../middleware/authMiddleware');

// 모든 admin 라우트에 JWT 인증 미들웨어 적용
router.use(auth);

// /api/v1/admin 라우트 정의
router.get('/stats', adminController.getStats);

module.exports = router;
