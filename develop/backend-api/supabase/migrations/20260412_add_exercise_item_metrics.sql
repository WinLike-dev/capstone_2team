alter table public.exercise_items
  add column if not exists target_sets integer,
  add column if not exists duration_minutes integer;
