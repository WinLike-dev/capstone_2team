const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const homeController = require('../controllers/homeController');

router.use(authMiddleware);

router.post('/recommendations', homeController.getRecommendations);
router.post('/recommendations/workout', homeController.getWorkoutRecommendations);
router.post('/recommendations/diet', homeController.getDietRecommendations);

module.exports = router;
