const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');

// 프로토타입: 인증 미들웨어 없음, 추후 관리자 권한 체크 추가 예정

// /api/v1/admin 라우트 정의
router.get('/stats', adminController.getStats);

module.exports = router;
