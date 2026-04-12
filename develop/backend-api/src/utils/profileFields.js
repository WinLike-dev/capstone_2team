function parseStoredArray(value) {
  if (Array.isArray(value)) {
    return value.filter((item) => item !== null && item !== undefined).map(String);
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) {
      return [];
    }

    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) {
        return parsed.filter((item) => item !== null && item !== undefined).map(String);
      }
    } catch (error) {
      return [trimmed];
    }

    return [];
  }

  return [];
}

function serializeArrayField(value) {
  return JSON.stringify(parseStoredArray(value));
}

function toOptionalNumber(value) {
  if (value === undefined) return undefined;
  if (value === null || value === '') return null;

  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

function toOptionalString(value) {
  if (value === undefined) return undefined;
  if (value === null) return null;

  const text = String(value).trim();
  return text ? text : null;
}

function normalizeProfileRow(profile = {}) {
  const normalized = {
    ...profile,
    allergies: parseStoredArray(profile.allergies),
    conditions: parseStoredArray(profile.medical_history),
    injury_history: parseStoredArray(profile.injury_history),
    medical_history: parseStoredArray(profile.medical_history),
  };

  if (profile.users && profile.users.nickname && !normalized.nickname) {
    normalized.nickname = profile.users.nickname;
  }

  delete normalized.users;
  return normalized;
}

module.exports = {
  normalizeProfileRow,
  parseStoredArray,
  serializeArrayField,
  toOptionalNumber,
  toOptionalString,
};
