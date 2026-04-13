create extension if not exists pgcrypto;

create table if not exists public.chat_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  client_message_id text not null,
  session_id text not null,
  user_message text not null,
  assistant_message text not null,
  rating text not null check (rating in ('up', 'down')),
  reason_codes text[] not null default '{}',
  comment text,
  intent text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists chat_feedback_user_message_uidx
  on public.chat_feedback (user_id, client_message_id);

create index if not exists chat_feedback_rating_created_idx
  on public.chat_feedback (rating, created_at desc);

create index if not exists chat_feedback_user_created_idx
  on public.chat_feedback (user_id, created_at desc);
