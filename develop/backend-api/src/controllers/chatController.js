const axios = require('axios');
const logger = require('../utils/logger');
const { buildDailySessionId } = require('../utils/kst');

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

// @route   POST /api/v1/chat
// @desc    WAS chat gateway -> FastAPI /chat
// @access  Private
exports.sendMessage = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const rawMessage = typeof req.body.user_message === 'string'
      ? req.body.user_message
      : req.body.message;
    const userMessage = rawMessage ? rawMessage.trim() : '';
    const requestedSessionId = typeof req.body.session_id === 'string'
      ? req.body.session_id.trim()
      : '';

    if (!userMessage) {
      return res.status(400).json({ error: 'message is required.' });
    }

    const sessionId = requestedSessionId || buildDailySessionId(userId);
    const payload = {
      user_id: userId,
      user_message: userMessage,
      session_id: sessionId,
    };

    const response = await axios.post(`${FASTAPI_URL}/chat`, payload, {
      timeout: AI_TIMEOUT,
      headers: buildFastApiHeaders(),
    });

    return res.json({
      ...response.data,
      session_id: response.data?.session_id || sessionId,
    });
  } catch (error) {
    const upstreamStatus = error.response?.status;
    const upstreamPayload = error.response?.data;

    logger.error('Chat gateway error: %s', error.message);

    if (upstreamStatus) {
      return res.status(502).json({
        error: 'FastAPI chat upstream error.',
        upstream_status: upstreamStatus,
        upstream_error: upstreamPayload || null,
      });
    }

    return res.status(500).json({
      error: 'Failed to process chat request.',
    });
  }
};
