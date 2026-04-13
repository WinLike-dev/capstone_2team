# Chat Feedback Feature

## 1. Feature Goal

The project now supports explicit feedback on assistant chat answers.

The design decision is:

- do not save every chat turn by default
- save only when the user explicitly clicks `like` or `dislike`

This reduces unnecessary storage and keeps the signal tied to real user judgment.

## 2. User Experience

Feedback is shown only for assistant messages that came from a real chat response.

Current UX:

- assistant response renders
- user sees `like` and `dislike` buttons under the answer
- `like` saves immediately
- `dislike` opens a modal
- the modal requires at least one reason or a comment
- after success, the message shows that feedback was saved

No feedback controls should appear for:

- the static welcome message
- streaming placeholders before completion
- messages without a `clientMessageId`

## 3. Frontend Implementation

Main file:

- `develop/frontend-ui/app/chat/page.tsx`

Important frontend details:

- each assistant message gets a local `clientMessageId`
- that id is generated in the browser
- the message also stores:
  - `sessionId`
  - `userMessage`
  - `intent`
  - feedback UI state

Reason codes currently implemented:

| Code | UI meaning |
| --- | --- |
| `not_helpful` | not helpful |
| `not_personalized` | does not fit my situation |
| `incorrect` | inaccurate content |
| `too_vague` | too vague |
| `tone_issue` | poor tone |
| `unsafe` | unsafe or uncomfortable |

Note:

- UI labels are Korean in the app
- database stores the stable English reason codes

## 4. Backend Implementation

Main files:

- `develop/backend-api/src/routes/chat.js`
- `develop/backend-api/src/controllers/chatController.js`

Routes:

- `POST /api/v1/chat`
- `POST /api/v1/chat/feedback`

Feedback payload fields:

```json
{
  "client_message_id": "uuid-or-local-id",
  "session_id": "user_id:YYYY-MM-DD",
  "user_message": "original user message",
  "assistant_message": "assistant answer snapshot",
  "rating": "up",
  "reason_codes": ["too_vague"],
  "comment": "optional",
  "intent": "optional"
}
```

Validation rules:

- `client_message_id` is required
- `user_message` is required
- `assistant_message` is required
- `rating` must be `up` or `down`
- every reason code must be from the approved set
- for `down`, at least one reason or a comment is required

Implementation detail that should not be removed casually:

- backend chat gateway uses `proxy: false` for the FastAPI call
- backend chat gateway resolves axios as `axiosModule.default || axiosModule`

These were needed to avoid local proxy and CommonJS runtime issues.

## 5. Database Schema

Migration file:

- `develop/backend-api/supabase/migrations/20260413034000_add_chat_feedback.sql`

Table:

- `public.chat_feedback`

Columns:

- `id uuid primary key`
- `user_id text not null`
- `client_message_id text not null`
- `session_id text not null`
- `user_message text not null`
- `assistant_message text not null`
- `rating text not null`
- `reason_codes text[] not null`
- `comment text null`
- `intent text null`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Indexes:

- unique `(user_id, client_message_id)`
- index on `(rating, created_at desc)`
- index on `(user_id, created_at desc)`

Current write strategy:

- backend uses `upsert`
- the same user can update feedback for the same assistant message id

## 6. End-To-End Data Flow

1. Frontend sends `POST /api/v1/chat`
2. Backend generates or preserves `session_id`
3. Backend calls FastAPI `/chat`
4. Frontend receives assistant text
5. Frontend creates `clientMessageId` for that assistant message
6. User clicks `like` or `dislike`
7. Frontend sends `POST /api/v1/chat/feedback`
8. Backend validates and upserts into Supabase

## 7. Known Limits

This is the current MVP, not the final analytics system.

Known limits:

- feedback exists only for responses the user explicitly rated
- there is no full chat transcript table yet
- `clientMessageId` is frontend-generated, not server-generated
- browser refresh behavior depends on current chat page state, not a separate persistent chat history UI

## 8. Verified Status

The following were already verified before this doc was written:

- backend route accepts valid feedback
- Supabase row is created successfully
- pushed deployment completed
- backend health check is live after deploy

What was not fully automated in this environment:

- browser click-by-click visual UI verification inside a local sandboxed browser run

That means the API and persistence path are verified, while final user acceptance remains a manual browser check.

## 9. Extension Ideas

Reasonable next steps if the team wants to expand this:

- add analytics dashboard by `rating`, `intent`, and `reason_codes`
- add per-model or per-persona quality breakdown
- persist chat transcript separately for opted-in users
- add admin export for poor feedback cases
- use downvoted examples to improve prompts or evaluation datasets
