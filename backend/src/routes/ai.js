const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController');
const auth = require('../middleware/authMiddleware');

// 모든 ai 라우트에 JWT 인증 적용
router.use(auth);

// 운동/식단 캘린더 데이터 조회
router.get('/plans', aiController.getPlans);

// 실시간 프롬프트 식단 분석 (AI 중계)
router.post('/diet-analyze', aiController.analyzeDiet);

module.exports = router;
