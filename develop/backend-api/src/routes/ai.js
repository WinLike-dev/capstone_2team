const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController');

// 프로토타입: 인증 미들웨어 없음, 추후 추가 예정

// 운동/식단 캘린더 데이터 조회 (기간별)
router.get('/plans', aiController.getPlans);

// 식단 기록 → AI 칼로리 분석 중계 (DataFormat_2_ai_api)
router.post('/meal-record', aiController.processMeal);

// 운동/식단 추천 요청 (DataFormat_2_ai_api)
router.post('/recommend', aiController.recommend);

// 사용자 지시사항 AI 서버로 전달 (DataFormat_2_ai_api)
router.post('/instruction', aiController.saveInstruction);

// 메인 홈 하트(추천) 클릭 시 기존 스케줄 연동 AI 재설계
router.post('/heart-recommend', aiController.heartRecommend);

module.exports = router;
