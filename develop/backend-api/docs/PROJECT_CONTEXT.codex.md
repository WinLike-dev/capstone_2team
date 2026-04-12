# Backend API Context

## Scope
- This service is the WAS layer between `frontend-ui` and `ai-model`.
- Stack: Express + Supabase.
- Frontend should call this service only.
- AI/FastAPI should also call this service through internal API routes.

## What This Service Owns
- JWT-protected app APIs for frontend.
- Internal APIs for AI read/write.
- Deterministic chat session id generation.
- Supabase persistence for profile, calendar, workout plans, meal plans.
- Persona settings update through a dedicated settings route.

## Main Entry Files
- `src/app.js`: route registration.
- `src/server.js`: server bootstrap.
- `src/config/db.js`: Supabase client.

## Public Frontend-Facing Routes
- `src/routes/auth.js`
- `src/routes/users.js`
- `src/routes/chat.js`
- `src/routes/home.js`

## Internal AI-Facing Routes
- Mounted under `app.use('/api', require('./routes/internal'))`
- Contract is aligned to `ai-model/v2/docs/was_api_contract.md`

## Current Key Contracts
- Chat path:
  - frontend -> `POST /api/v1/chat` -> FastAPI `POST /chat`
- Home recommendation path:
  - frontend -> `POST /api/v1/home/recommendations` -> FastAPI `POST /home/recommendations`
- FastAPI internal auth:
  - send `x-api-key`
- Chat session rule:
  - `session_id = user_id:YYYY-MM-DD`
  - KST basis
  - implemented in `src/utils/kst.js`
- `selected_ai_persona` update path:
  - `PATCH /api/v1/users/:user_id/settings/persona`
  - do not allow it through general profile save or AI natural language writes

## Important Controllers
- `src/controllers/chatController.js`
  - Builds deterministic daily `session_id`
  - Sends `{ user_id, user_message, session_id }` to FastAPI
- `src/controllers/homeController.js`
  - Forwards `{ user_id, type }` to FastAPI home recommendation endpoint
- `src/controllers/userController.js`
  - Frontend profile/calendar/recommend add-replace APIs
- `src/controllers/internalController.js`
  - AI-facing internal read/write plan/profile APIs

## Recommendation-Related Rules
- Workout recommendation add:
  - `POST /api/v1/users/exercises/recommend-add`
  - Adds to today's workout plan tail
  - supports `target_sets`, `duration_minutes`, `calories`
- Diet recommendation apply:
  - `PUT /api/v1/users/meals/recommend-replace`
  - Replaces today's slot, not duplicates it
  - supports `calories`

## Current Data Assumptions
- Workout categories are canonical:
  - `upper_body`, `lower_body`, `cardio`, `stretching`
- Diet categories are canonical:
  - `breakfast`, `lunch`, `dinner`
- Day format is always `YYYY-MM-DD`
- Plan update semantics:
  - full replace for dates included in payload

## Supabase Notes
- Migration folder:
  - `supabase/migrations/`
- Important recent schema expectations:
  - `user_health_profiles.selected_ai_persona`
  - `user_health_profiles.diet_type`
  - `user_health_profiles.injury_history`
  - `user_meal_plans.calories`
  - `exercise_items.target_sets`
  - `exercise_items.duration_minutes`

## Files To Touch For Common Tasks
- New frontend API:
  - route file in `src/routes`
  - controller in `src/controllers`
  - app mount in `src/app.js` if new top-level group
- AI internal contract change:
  - `src/routes/internal.js`
  - `src/controllers/internalController.js`
- Persona or profile policy:
  - `src/controllers/userController.js`
  - `src/utils/profileFields.js`
- Chat session policy:
  - `src/controllers/chatController.js`
  - `src/utils/kst.js`

## Change Guardrails
- Do not let frontend call FastAPI directly.
- Do not remove `x-api-key` forwarding to FastAPI.
- Do not make `selected_ai_persona` writable through general profile save.
- Do not change date format back to weekday strings.
- Keep home recommendation routes separate from chat routes.
