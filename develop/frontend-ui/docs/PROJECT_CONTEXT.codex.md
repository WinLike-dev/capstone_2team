# Frontend UI Context

## Scope
- This is the Next.js app shown to users.
- It must talk to `backend-api`, not directly to `ai-model`.
- Main tabs currently include home, chat, profile, and related onboarding/auth screens.

## Main Responsibilities
- Render calendar/home/chat/profile screens.
- Keep auth token in local storage.
- Fetch real profile and plan data from `backend-api`.
- Render AI home recommendations and let user apply them.

## Main Entry Files
- `app/page.tsx`: home tab and AI recommendation UI.
- `app/chat/page.tsx`: chat UI.
- `app/context/PlanContext.tsx`: plan/profile fetch and mutation layer.
- `lib/homeRecommendations.ts`: home recommendation cache and local helpers.
- `lib/date.ts`: KST date helpers for UI cache keys and display.

## Current Communication Rules
- Chat:
  - call `POST /api/v1/chat`
  - send `{ message }`
  - backend translates to FastAPI contract
- Home recommendations:
  - initial load: call `POST /api/v1/home/recommendations/workout` then `POST /api/v1/home/recommendations/diet`
  - workout refresh: call `POST /api/v1/home/recommendations/workout`
  - diet refresh: call `POST /api/v1/home/recommendations/diet`
  - send `{ recent_recommendations }`
- Profile/calendar:
  - call `backend-api` user routes only

## Home Recommendation UI Rules
- First entry to home tab on a KST day:
  - request workout first, then diet
- Workout refresh button:
  - request workout endpoint only
- Diet refresh button:
  - request diet endpoint only
- Cache:
  - localStorage
  - one day per user, KST-based
- Added state:
  - after user applies a recommendation, keep the card in disabled `added` state
  - only clear that state when the relevant refresh is pressed

## Workout/Diet Recommendation Shape
- Workout slots:
  - `upper_body`
  - `lower_body`
  - `cardio`
  - `stretching`
- Diet slots:
  - `breakfast`
  - `lunch`
  - `dinner`
- Workout display rules:
  - show `sets` for `upper_body`, `lower_body`, `stretching`
  - show `duration_minutes` for `cardio`
- Slot values may be `null`

## PlanContext Responsibilities
- Fetch profile from backend.
- Fetch calendar/plan data from backend.
- Normalize backend response into UI-friendly `DailyPlan`.
- Apply recommendation actions:
  - add workout to today's list
  - replace meal slot for today

## Important Current Source Of Truth Rules
- Real plan data comes from backend/Supabase.
- Do not reintroduce mock/localStorage as plan source of truth.
- localStorage is allowed only for:
  - auth token
  - home recommendation daily cache
  - home recommendation added-state cache

## Files To Touch For Common Tasks
- Home recommendation UI:
  - `app/page.tsx`
  - `lib/homeRecommendations.ts`
- Calendar or today-plan rendering:
  - `app/context/PlanContext.tsx`
- Chat UI:
  - `app/chat/page.tsx`
- Shared date or cache behavior:
  - `lib/date.ts`

## Change Guardrails
- Do not call FastAPI directly from the browser.
- Do not store final workout/meal plan state only in localStorage.
- Keep backend route usage aligned with JWT auth headers.
- Keep workout taxonomy aligned with backend and AI:
  - `upper_body`, `lower_body`, `cardio`, `stretching`
- Keep diet taxonomy aligned:
  - `breakfast`, `lunch`, `dinner`
