const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController');
const auth = require('../middleware/authMiddleware');

// 모든 ai 라우트에 JWT 인증 적용
router.use(auth);

// 운동/식단 캘린더 데이터 조회 (기간별)
router.get('/plans', aiController.getPlans);

// 식단 기록 → AI 칼로리 분석 중계 (DataFormat_2_ai_api)
router.post('/process-meal', aiController.processMeal);

// 운동/식단 추천 요청 (DataFormat_2_ai_api)
router.post('/recommend', aiController.recommend);

module.exports = router;
