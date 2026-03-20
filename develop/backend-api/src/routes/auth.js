const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

// /api/v1/auth 라우트 정의
router.post('/register', authController.register);
router.post('/login', authController.login);
router.post('/logout', authController.logout);

module.exports = router;
