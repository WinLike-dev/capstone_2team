-- v2 contract alignment
-- Target date: 2026-04-12

alter table if exists public.user_health_profiles
  add column if not exists diet_type text,
  add column if not exists injury_history text,
  add column if not exists selected_ai_persona text;

update public.user_health_profiles
set selected_ai_persona = coalesce(nullif(selected_ai_persona, ''), 'default')
where selected_ai_persona is null or selected_ai_persona = '';

alter table if exists public.user_meal_plans
  add column if not exists calories integer default 0;

update public.user_meal_plans
set calories = coalesce(calories, 0)
where calories is null;
