const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const { createClient } = require('../../develop/backend-api/node_modules/@supabase/supabase-js');
require('../../develop/backend-api/node_modules/dotenv').config({
  path: path.resolve(__dirname, '../../develop/backend-api/.env'),
});

const BACKEND_URL = 'https://34.50.45.68.nip.io';
const REPORT_DIR = path.resolve(__dirname, '../reports');
const REPORT_PATH = path.join(REPORT_DIR, 'approval_bottleneck_report.json');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

const PERSONA = {
  label: '20대 청년 직장인',
  genderApi: 'male',
  age: 24,
  height: 178,
  weight: 72,
  goal: '근력 향상',
  activityLevel: '보통',
  mbti: 'ENTJ',
  conditions: ['없음'],
  allergies: ['해당 없음'],
  planPrompt: '내 상황에 맞게 오늘 운동과 식단 계획을 짜줘.',
  modifyPrompt: '운동 시간을 45분 이내로 줄이고 점심은 더 가볍게 수정해줘.',
};

const APPROVAL_VARIANTS = [
  '좋아요. 방금 수정한 계획으로 진행해줘.',
  '좋아요. 이제 이 계획을 확정하고 반영해줘.',
  '수정된 계획 확인했어. 그대로 적용해줘.',
  '오케이. 이 계획으로 오늘 일정에 반영해줘.',
];

function nowIso() {
  return new Date().toISOString();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function excerpt(value, maxLength = 200) {
  if (!value) return '';
  const text = String(value).replace(/\s+/g, ' ').trim();
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function createSeed() {
  const stamp = Date.now();
  return {
    loginId: `approval_probe_${stamp}`,
    password: 'Playwright123!',
    nickname: `승인${String(stamp).slice(-5)}`,
    email: `approval_probe_${stamp}@example.com`,
  };
}

async function postJson(url, payload, token = null) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  const body = await response.json().catch(() => ({}));
  return {
    status: response.status,
    ok: response.ok,
    body,
  };
}

async function createAndLoginUser() {
  const seed = createSeed();

  const signup = await postJson(`${BACKEND_URL}/api/v1/auth/signup`, {
    login_id: seed.loginId,
    password: seed.password,
    nickname: seed.nickname,
    email: seed.email,
  });
  expect(signup.status).toBe(201);

  const login = await postJson(`${BACKEND_URL}/api/v1/auth/login`, {
    login_id: seed.loginId,
    password: seed.password,
  });
  expect(login.status).toBe(200);

  const token = login.body?.token;
  const userId = login.body?.user?.user_id;

  expect(token).toBeTruthy();
  expect(userId).toBeTruthy();

  const profile = await postJson(`${BACKEND_URL}/api/v1/users/profile`, {
    user_id: userId,
    nickname: seed.nickname,
    mbti: PERSONA.mbti,
    gender: PERSONA.genderApi,
    age: PERSONA.age,
    height: PERSONA.height,
    weight: PERSONA.weight,
    bmi: 0,
    goal: PERSONA.goal,
    activity_level: PERSONA.activityLevel,
    medical_history: PERSONA.conditions,
    allergies: PERSONA.allergies,
  }, token);
  expect(profile.status).toBe(200);

  return {
    seed,
    token,
    userId,
  };
}

async function postChat(token, message, sessionId) {
  return postJson(`${BACKEND_URL}/api/v1/chat`, {
    message,
    session_id: sessionId,
  }, token);
}

async function getPlanSnapshot(userId) {
  const [exerciseResult, mealResult] = await Promise.all([
    supabase
      .from('user_exercise_plans')
      .select('exercise_id, created_at, target_date')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(20),
    supabase
      .from('user_meal_plans')
      .select('meal_id, created_at, target_date')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(20),
  ]);

  if (exerciseResult.error) throw exerciseResult.error;
  if (mealResult.error) throw mealResult.error;

  const exerciseRows = exerciseResult.data || [];
  const mealRows = mealResult.data || [];

  return {
    exerciseCount: exerciseRows.length,
    mealCount: mealRows.length,
    exerciseIds: exerciseRows.map((row) => row.exercise_id),
    mealIds: mealRows.map((row) => row.meal_id),
    latestExerciseCreatedAt: exerciseRows[0]?.created_at || null,
    latestMealCreatedAt: mealRows[0]?.created_at || null,
  };
}

function hasPlanSnapshotAdvanced(baseline, next) {
  const baselineExerciseIds = new Set(baseline.exerciseIds || []);
  const baselineMealIds = new Set(baseline.mealIds || []);

  const hasNewExerciseId = (next.exerciseIds || []).some((id) => !baselineExerciseIds.has(id));
  const hasNewMealId = (next.mealIds || []).some((id) => !baselineMealIds.has(id));
  if (hasNewExerciseId || hasNewMealId) {
    return true;
  }

  const baselineExerciseTs = baseline.latestExerciseCreatedAt
    ? Date.parse(baseline.latestExerciseCreatedAt)
    : 0;
  const baselineMealTs = baseline.latestMealCreatedAt
    ? Date.parse(baseline.latestMealCreatedAt)
    : 0;
  const nextExerciseTs = next.latestExerciseCreatedAt
    ? Date.parse(next.latestExerciseCreatedAt)
    : 0;
  const nextMealTs = next.latestMealCreatedAt
    ? Date.parse(next.latestMealCreatedAt)
    : 0;

  return nextExerciseTs > baselineExerciseTs || nextMealTs > baselineMealTs;
}

async function waitForPlanWrite(userId, baseline, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const next = await getPlanSnapshot(userId);
    if (hasPlanSnapshotAdvanced(baseline, next)) {
      return next;
    }
    await sleep(1000);
  }
  return null;
}

test.describe('Approval bottleneck probe', () => {
  test.setTimeout(300000);

  test('isolates approval routing vs DB write', async () => {
    const report = {
      startedAt: nowIso(),
      backendUrl: BACKEND_URL,
      persona: PERSONA.label,
      user: null,
      variants: [],
      finishedAt: null,
    };

    try {
      const auth = await createAndLoginUser();
      report.user = {
        userId: auth.userId,
        loginId: auth.seed.loginId,
      };

      for (let index = 0; index < APPROVAL_VARIANTS.length; index += 1) {
        const approvalPrompt = APPROVAL_VARIANTS[index];
        const sessionId = `approval_probe_${auth.userId}_${Date.now()}_${index + 1}`;
        const baseline = await getPlanSnapshot(auth.userId);

        const plan = await postChat(auth.token, PERSONA.planPrompt, sessionId);
        const modify = await postChat(auth.token, PERSONA.modifyPrompt, sessionId);
        const approval = await postChat(auth.token, approvalPrompt, sessionId);
        const nextSnapshot = await waitForPlanWrite(auth.userId, baseline, 35000);

        report.variants.push({
          approvalPrompt,
          sessionId,
          baselineSnapshot: baseline,
          plan: {
            status: plan.status,
            intent: plan.body?.intent || null,
            response: excerpt(plan.body?.response),
            error: plan.ok ? null : plan.body || null,
          },
          modify: {
            status: modify.status,
            intent: modify.body?.intent || null,
            response: excerpt(modify.body?.response),
            error: modify.ok ? null : modify.body || null,
          },
          approval: {
            status: approval.status,
            intent: approval.body?.intent || null,
            response: excerpt(approval.body?.response),
            error: approval.ok ? null : approval.body || null,
          },
          planWriteObserved: Boolean(nextSnapshot),
          finalSnapshot: nextSnapshot || baseline,
        });
      }
    } finally {
      report.finishedAt = nowIso();
      fs.mkdirSync(REPORT_DIR, { recursive: true });
      fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2), 'utf8');
    }

    expect(fs.existsSync(REPORT_PATH)).toBeTruthy();
  });
});
