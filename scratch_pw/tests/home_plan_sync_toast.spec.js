const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.PW_BASE_URL || 'http://localhost:3000';
const REPORT_PATH = path.resolve(
  __dirname,
  '../reports/home_plan_sync_toast_report.json'
);

function formatKstDate(date = new Date()) {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

function emptyAddedState() {
  return {
    workout: {
      upper_body: false,
      lower_body: false,
      cardio: false,
      stretching: false,
    },
    diet: {
      breakfast: false,
      lunch: false,
      dinner: false,
    },
  };
}

function emptyHistory() {
  return {
    workout: {
      upper_body: [],
      lower_body: [],
      cardio: [],
      stretching: [],
    },
    diet: {
      breakfast: [],
      lunch: [],
      dinner: [],
    },
  };
}

function recommendationsFor(today) {
  return {
    workout: {
      date: today,
      scope: 'workout',
      workout: {
        upper_body: {
          exercise_name: '테스트 푸시업',
          summary: '가슴과 코어를 깨우는 짧은 루틴',
          sets: 3,
          duration_minutes: null,
          calories: 123,
        },
        lower_body: {
          exercise_name: '테스트 스쿼트',
          summary: '하체 균형을 잡는 기본 루틴',
          sets: 3,
          duration_minutes: null,
          calories: 150,
        },
        cardio: {
          exercise_name: '테스트 빠른 걷기',
          summary: '가볍게 심박수를 올리는 유산소',
          sets: null,
          duration_minutes: 20,
          calories: 180,
        },
        stretching: {
          exercise_name: '테스트 전신 스트레칭',
          summary: '긴장을 풀어주는 마무리 루틴',
          sets: 2,
          duration_minutes: null,
          calories: 60,
        },
      },
      diet: {
        breakfast: null,
        lunch: null,
        dinner: null,
      },
    },
    diet: {
      date: today,
      scope: 'diet',
      workout: {
        upper_body: null,
        lower_body: null,
        cardio: null,
        stretching: null,
      },
      diet: {
        breakfast: {
          food_name: '테스트 오트밀',
          summary: '단백질과 식이섬유를 함께 챙기는 아침',
          calories: 360,
        },
        lunch: {
          food_name: '테스트 닭가슴살 샐러드',
          summary: '점심 단백질 보충 식단',
          calories: 480,
        },
        dinner: {
          food_name: '테스트 연어 구이',
          summary: '가벼운 저녁 회복 식단',
          calories: 520,
        },
      },
    },
  };
}

async function seedLocalAuth(page, today) {
  await page.addInitScript(
    ({ currentDate }) => {
      if (sessionStorage.getItem('__pwPlanToastSeeded') === 'true') return;

      const user = {
        user_id: 'pw-plan-toast-user',
        login_id: 'pw-plan-toast-user',
        nickname: '테스터',
        email: 'pw-plan-toast@example.com',
        goal: '체중 관리',
        gender: 'female',
        age: 32,
        height: 165,
        weight: 58,
        activityLevel: '보통',
        has_health_profile: true,
      };

      localStorage.clear();
      localStorage.setItem('healthAppToken', 'pw-token');
      localStorage.setItem('healthAppUser', JSON.stringify(user));
      localStorage.setItem(
        `healthAppHomeRecommendations:${user.user_id}:${currentDate}`,
        JSON.stringify({
          recommendations: {
            date: currentDate,
            scope: 'all',
            workout: {
              upper_body: null,
              lower_body: null,
              cardio: null,
              stretching: null,
            },
            diet: {
              breakfast: null,
              lunch: null,
              dinner: null,
            },
          },
          added: {
            workout: {
              upper_body: false,
              lower_body: false,
              cardio: false,
              stretching: false,
            },
            diet: {
              breakfast: false,
              lunch: false,
              dinner: false,
            },
          },
          history: {
            workout: {
              upper_body: [],
              lower_body: [],
              cardio: [],
              stretching: [],
            },
            diet: {
              breakfast: [],
              lunch: [],
              dinner: [],
            },
          },
        })
      );
      sessionStorage.setItem('__pwPlanToastSeeded', 'true');
    },
    { currentDate: today }
  );
}

async function mockApi(page, today) {
  const recs = recommendationsFor(today);
  const calendarState = {
    exerciseItems: [],
    mealItems: [],
  };
  const report = {
    calendarFetchCount: 0,
    recommendAddCount: 0,
    unknownRequests: [],
  };

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname;

    if (pathname === '/api/v1/users/profile') {
      await route.fulfill({
        status: 200,
        json: {
          user_id: 'pw-plan-toast-user',
          login_id: 'pw-plan-toast-user',
          nickname: '테스터',
          email: 'pw-plan-toast@example.com',
          goal: '체중 관리',
          gender: 'female',
          age: 32,
          height: 165,
          weight: 58,
          activity_level: '보통',
          has_health_profile: true,
        },
      });
      return;
    }

    if (pathname === '/api/v1/users/calendar') {
      report.calendarFetchCount += 1;
      await route.fulfill({
        status: 200,
        json: {
          [today]: {
            exercises: calendarState.exerciseItems.length
              ? [
                  {
                    exercise_id: 901,
                    exercise_type: 'upper_body',
                    total_calories: 123,
                    status: 0,
                    target_date: today,
                    exercise_items: calendarState.exerciseItems,
                  },
                ]
              : [],
            meals: calendarState.mealItems,
          },
        },
      });
      return;
    }

    if (pathname === '/api/v1/home/recommendations/workout') {
      await route.fulfill({ status: 200, json: recs.workout });
      return;
    }

    if (pathname === '/api/v1/home/recommendations/diet') {
      await route.fulfill({ status: 200, json: recs.diet });
      return;
    }

    if (pathname === '/api/v1/users/exercises/recommend-add') {
      report.recommendAddCount += 1;
      calendarState.exerciseItems = [
        {
          item_id: 7001,
          exercise_name: '테스트 푸시업',
          is_completed: false,
          calories: 123,
          target_sets: 3,
          duration_minutes: null,
        },
      ];
      await route.fulfill({
        status: 200,
        json: { ok: true, item_id: 7001 },
      });
      return;
    }

    report.unknownRequests.push({
      method: request.method(),
      pathname,
    });
    await route.fulfill({ status: 404, json: { error: 'unmocked' } });
  });

  return report;
}

test('home accepted workout recommendation shows toast, opens plan, and clears highlight', async ({
  page,
}) => {
  test.setTimeout(90000);

  const today = formatKstDate();
  await seedLocalAuth(page, today);
  const report = await mockApi(page, today);

  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('테스트 푸시업').first()).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByLabel('상체 운동 추천 추가')).toBeVisible({
    timeout: 30000,
  });

  await page.getByLabel('상체 운동 추천 추가').click();
  await page.locator('div.fixed.inset-0 button.bg-blue-600').click();

  const toast = page.getByTestId('plan-sync-toast');
  await expect(toast).toBeVisible({ timeout: 10000 });
  await expect(toast).toContainText('운동이 오늘 플랜에 추가됐어요');
  await expect(toast).toContainText('테스트 푸시업');

  const homeHighlight = page.getByText('방금 반영됨').first();
  await expect(homeHighlight).toBeVisible();

  await page.getByTestId('plan-sync-toast-plan-link').click();
  await expect(page).toHaveURL(/\/recommend$/);

  const tabUpdateDot = page.locator('[aria-label="변경된 플랜 있음"]');
  await expect(tabUpdateDot).toBeVisible();

  const highlightedPlanItem = page.locator('[data-plan-update-highlight="true"]');
  await expect(highlightedPlanItem.first()).toBeVisible();
  await expect(page.getByText('테스트 푸시업').first()).toBeVisible();

  await highlightedPlanItem.first().hover();
  await expect(page.locator('[data-plan-update-highlight="true"]')).toHaveCount(0);
  await expect(tabUpdateDot).toHaveCount(0);

  const finalReport = {
    ...report,
    passed: true,
    today,
  };
  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, JSON.stringify(finalReport, null, 2));
});
