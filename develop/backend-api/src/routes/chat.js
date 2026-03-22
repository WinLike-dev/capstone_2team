const express = require('express');
const router = express.Router();
const chatController = require('../controllers/chatController');

// 프로토타입: 인증 미들웨어 없음, 추후 추가 예정

// AI 채팅 메시지 전송 (DataFormat_3_ai)
router.post('/', chatController.sendMessage);

module.exports = router;
