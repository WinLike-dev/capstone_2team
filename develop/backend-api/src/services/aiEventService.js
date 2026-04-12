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

exports.notifyProfileUpdated = async (userId, changedFields = [], profileVersion = null) => {
  try {
    const payload = {
      user_id: userId,
      changed_fields: changedFields,
    };

    if (profileVersion !== null) {
      payload.profile_version = profileVersion;
    }

    const response = await axios.post(
      `${FASTAPI_URL}/internal/events/profile-updated`,
      payload,
      {
        timeout: AI_TIMEOUT,
        headers: buildFastApiHeaders(),
      }
    );

    logger.info(
      'Profile update event pushed: user_id=%s fields=%s',
      userId,
      changedFields.join(',')
    );
    return response.data;
  } catch (error) {
    logger.error(
      'Profile update event push failed: user_id=%s error=%s',
      userId,
      error.message
    );
    return null;
  }
};
