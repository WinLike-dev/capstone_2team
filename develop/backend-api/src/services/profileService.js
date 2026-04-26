const {
  normalizeProfileRow,
  serializeArrayField,
  toOptionalString,
} = require('../utils/profileFields');

const DEFAULT_SELECTED_AI_PERSONA = 'default';

function buildDefaultProfileSeed(userId) {
  return {
    user_id: userId,
    gender: 'unknown',
    age: 0,
    height: 0,
    weight: 0,
    bmi: 0,
    allergies: '[]',
    injury_history: '[]',
    medical_history: '[]',
    selected_ai_persona: DEFAULT_SELECTED_AI_PERSONA,
  };
}

function coerceRequiredNumber(value, fallback = 0) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function normalizeStoredArrayField(value) {
  if (value === undefined) {
    return '[]';
  }

  return serializeArrayField(value);
}

function buildNormalizedProfile(userId, profile = {}, nickname = null) {
  const normalized = normalizeProfileRow({
    user_id: userId,
    weight: 0,
    height: 0,
    age: 0,
    gender: 'unknown',
    diet_type: null,
    allergies: '[]',
    injury_history: '[]',
    goal: null,
    activity_level: null,
    selected_ai_persona: DEFAULT_SELECTED_AI_PERSONA,
    bmi: 0,
    medical_history: '[]',
    mbti: null,
    ...profile,
    users: nickname ? { nickname } : undefined,
  });

  if (!normalized.selected_ai_persona) {
    normalized.selected_ai_persona = DEFAULT_SELECTED_AI_PERSONA;
  }

  return normalized;
}

function hasCompletedHealthProfile(profile = {}) {
  const normalized = normalizeProfileRow(profile);

  const age = Number(normalized.age || 0);
  const height = Number(normalized.height || 0);
  const weight = Number(normalized.weight || 0);
  const gender = String(normalized.gender || '').trim().toLowerCase();
  const goal = toOptionalString(normalized.goal);
  const activityLevel = toOptionalString(normalized.activity_level);
  const mbti = toOptionalString(normalized.mbti);
  const allergies = Array.isArray(normalized.allergies) ? normalized.allergies : [];
  const conditions = Array.isArray(normalized.medical_history)
    ? normalized.medical_history
    : Array.isArray(normalized.conditions)
      ? normalized.conditions
      : [];

  return (
    age > 0 &&
    height > 0 &&
    weight > 0 &&
    !!goal &&
    !!activityLevel &&
    !!mbti &&
    !!gender &&
    gender !== 'unknown' &&
    allergies.length > 0 &&
    conditions.length > 0
  );
}

async function loadUserSnapshot(supabase, userId) {
  const { data, error } = await supabase
    .from('users')
    .select('user_id, nickname')
    .eq('user_id', userId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

async function bootstrapProfileRow(supabase, userId) {
  const seed = buildDefaultProfileSeed(userId);
  const { data, error } = await supabase
    .from('user_health_profiles')
    .upsert(seed, { onConflict: 'user_id' })
    .select('*')
    .single();

  if (error) throw error;
  return data;
}

async function ensureUserHealthProfileRow(supabase, userId) {
  const user = await loadUserSnapshot(supabase, userId);
  if (!user) {
    return null;
  }

  const { data: profile, error } = await supabase
    .from('user_health_profiles')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();

  if (error) throw error;

  if (profile) {
    return profile;
  }

  return bootstrapProfileRow(supabase, userId);
}

function buildProfileRowForUpsert(userId, currentProfile = {}, patch = {}) {
  const merged = {
    ...buildDefaultProfileSeed(userId),
    ...currentProfile,
    ...patch,
    user_id: userId,
  };

  merged.gender = toOptionalString(merged.gender) ?? 'unknown';
  merged.age = coerceRequiredNumber(merged.age, 0);
  merged.height = coerceRequiredNumber(merged.height, 0);
  merged.weight = coerceRequiredNumber(merged.weight, 0);
  merged.bmi = coerceRequiredNumber(merged.bmi, 0);
  merged.allergies = normalizeStoredArrayField(merged.allergies);
  merged.injury_history = normalizeStoredArrayField(merged.injury_history);
  merged.medical_history = normalizeStoredArrayField(merged.medical_history);
  merged.selected_ai_persona =
    toOptionalString(merged.selected_ai_persona) ?? DEFAULT_SELECTED_AI_PERSONA;
  merged.goal = toOptionalString(merged.goal);
  merged.activity_level = toOptionalString(merged.activity_level);
  merged.diet_type = toOptionalString(merged.diet_type);
  merged.mbti = toOptionalString(merged.mbti);

  delete merged.updated_at;
  delete merged.users;
  delete merged.conditions;
  delete merged.nickname;

  return merged;
}

async function ensureUserHealthProfile(supabase, userId) {
  const user = await loadUserSnapshot(supabase, userId);
  if (!user) {
    return null;
  }

  const profile = await ensureUserHealthProfileRow(supabase, userId);
  if (!profile) {
    return null;
  }

  return buildNormalizedProfile(userId, profile, user.nickname || null);
}

module.exports = {
  DEFAULT_SELECTED_AI_PERSONA,
  buildDefaultProfileSeed,
  buildProfileRowForUpsert,
  buildNormalizedProfile,
  bootstrapProfileRow,
  ensureUserHealthProfile,
  ensureUserHealthProfileRow,
  hasCompletedHealthProfile,
  loadUserSnapshot,
};
