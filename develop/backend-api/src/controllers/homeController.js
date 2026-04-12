const axios = require('axios');
const logger = require('../utils/logger');

const FASTAPI_URL = (process.env.FASTAPI_URL || 'http://localhost:8000').replace(/\/$/, '');
const AI_TIMEOUT = parseInt(process.env.AI_REQUEST_TIMEOUT || '30000', 10);
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY || '';

function buildFastApiHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (INTERNAL_API_KEY) {
    headers['x-api-key'] = INTERNAL_API_KEY;
  }

  return headers;
}

// @route   POST /api/v1/home/recommendations
// @desc    Home tab recommendation gateway -> FastAPI /home/recommendations
// @access  Private
exports.getRecommendations = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const scope = String(req.body.type || 'all').trim().toLowerCase();

    if (!['all', 'workout', 'diet'].includes(scope)) {
      return res.status(400).json({ error: 'type must be one of all, workout, diet.' });
    }

    const response = await axios.post(
      `${FASTAPI_URL}/home/recommendations`,
      {
        user_id: userId,
        type: scope,
      },
      {
        timeout: AI_TIMEOUT,
        headers: buildFastApiHeaders(),
      }
    );

    return res.json(response.data);
  } catch (error) {
    const upstreamStatus = error.response?.status;
    const upstreamPayload = error.response?.data;

    logger.error('Home recommendation gateway error: %s', error.message);

    if (upstreamStatus) {
      return res.status(502).json({
        error: 'FastAPI home recommendation upstream error.',
        upstream_status: upstreamStatus,
        upstream_error: upstreamPayload || null,
      });
    }

    return res.status(500).json({
      error: 'Failed to load home recommendations.',
    });
  }
};
