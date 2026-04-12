const KST_TIME_ZONE = 'Asia/Seoul';
const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

function formatKstDate(date = new Date()) {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: KST_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

function buildDailySessionId(userId, date = new Date()) {
  return `${userId}:${formatKstDate(date)}`;
}

function normalizeIsoDate(value) {
  if (!value) return null;

  const text = String(value).trim();
  if (ISO_DATE_PATTERN.test(text)) {
    return text;
  }

  const normalized = text.replace(/[./]/g, '-');
  if (ISO_DATE_PATTERN.test(normalized)) {
    return normalized;
  }

  return null;
}

module.exports = {
  KST_TIME_ZONE,
  buildDailySessionId,
  formatKstDate,
  normalizeIsoDate,
};
