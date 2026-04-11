# AI Model Context

## Scope
- Active service is `v2`.
- Ignore `v1` unless someone explicitly asks for legacy behavior.
- This folder is the FastAPI + LangGraph side of the system.

## What This Service Owns
- `POST /chat`: AI chat generation through LangGraph.
- `POST /home/recommendations`: home-tab workout/diet recommendation generation.
- `POST /internal/events/profile-updated`: profile refresh event from WAS.
- Reading profile and plan data from WAS internal APIs.
- Writing approved plan/profile/check changes back to WAS through background/internal calls.

## Main Entry Files
- `v2/app/main.py`: FastAPI app and router registration.
- `v2/app/core/lifespan.py`: client initialization, graph compilation, checkpointer setup.
- `v2/app/routers/chat.py`: chat entrypoint and checkpoint resume logic.
- `v2/app/routers/home.py`: home recommendation entrypoint.
- `v2/app/routers/profile_events.py`: profile update event receiver.
- `v2/app/graph/builder.py`: LangGraph flow wiring.

## Current Graph Rules
- Chat flow:
  - `preprocess -> analyze_intent -> route -> generate -> persona`
- Home recommendation flow:
  - `preprocess -> analyze_intent -> generate -> END`
  - It uses `request_kind=home_recommendation`.
  - It bypasses `persona`.
- State schema:
  - `v2/app/schemas/state.py`
  - Home-specific fields are `request_kind`, `home_recommendation_scope`, `home_recommendations`.

## Critical External Contracts
- Caller is `backend-api`, not the frontend directly.
- Internal auth uses `x-api-key`.
- Chat session id is owned by WAS and must follow:
  - `session_id = user_id:YYYY-MM-DD`
  - Date basis is `Asia/Seoul`.
- Day format across plan APIs is always `YYYY-MM-DD`.
- `selected_ai_persona` is read-only here.
  - AI must not change it from natural language.
  - AI reads it from WAS profile only.

## Home Recommendation Contract
- Request path:
  - `POST /home/recommendations`
- Request body:
  - `user_id`
  - `type = all | workout | diet`
- Exclusion rule:
  - Exclude only today's existing plan items.
- Workout output slots:
  - `upper_body`
  - `lower_body`
  - `cardio`
  - `stretching`
- Diet output slots:
  - `breakfast`
  - `lunch`
  - `dinner`
- Slot values can be `null`.
- Workout prescription rules:
  - `upper_body`, `lower_body`, `stretching` use `sets`
  - `cardio` uses `duration_minutes`

## Important Files For Recommendation Work
- `v2/app/routers/home.py`
- `v2/app/graph/nodes/generate.py`
- `v2/app/services/home_recommendations.py`
- `v2/app/prompts/home/recommendations.md`
- `v2/app/schemas/home.py`

## Important Files For Chat/Plan Work
- `v2/app/routers/chat.py`
- `v2/app/graph/nodes/preprocess.py`
- `v2/app/graph/nodes/intent.py`
- `v2/app/graph/nodes/generate.py`
- `v2/app/graph/nodes/record.py`
- `v2/app/graph/nodes/was_write.py`
- `v2/app/schemas/llm_responses.py`
- `v2/app/schemas/was.py`

## WAS Read/Write Expectations
- Reads:
  - `/api/user/profile/{user_id}`
  - `/api/plan/today/{user_id}`
  - `/api/workout-plan/full/{user_id}`
  - `/api/diet-plan/full/{user_id}`
- Writes:
  - `/api/user/profile/{user_id}`
  - `/api/plan/check/{user_id}`
  - `/api/plan/create/{user_id}`
  - `/api/plan/update/{user_id}`

## Change Guardrails
- Do not reintroduce direct frontend-to-FastAPI coupling.
- Do not let AI write `selected_ai_persona`.
- Keep workout taxonomy aligned with frontend and backend:
  - `upper_body`, `lower_body`, `cardio`, `stretching`
- Keep diet taxonomy aligned:
  - `breakfast`, `lunch`, `dinner`
- Keep `home/recommendations` separate from chat entrypoint, but inside the same graph/runtime.

## First Documents To Read Before Editing
- `v2/docs/api_specification.md`
- `v2/docs/was_api_contract.md`
- `v2/docs/profile_sync_flow.md`
- `v2/docs/was_test_scenarios.md`
