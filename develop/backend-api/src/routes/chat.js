const express = require('express');
const router = express.Router();
const chatController = require('../controllers/chatController');
const auth = require('../middleware/authMiddleware');

// 모든 chat 라우트에 JWT 인증 미들웨어 적용
router.use(auth);

// /api/v1/chat 라우트 정의
router.post('/', chatController.sendMessage);
router.get('/history', chatController.getHistory);

module.exports = router;
