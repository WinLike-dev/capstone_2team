const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const homeController = require('../controllers/homeController');

router.use(authMiddleware);

router.post('/recommendations', homeController.getRecommendations);

module.exports = router;
