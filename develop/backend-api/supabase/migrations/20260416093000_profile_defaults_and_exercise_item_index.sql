alter table if exists public.user_health_profiles
  alter column selected_ai_persona set default 'default',
  alter column allergies set default '[]',
  alter column injury_history set default '[]',
  alter column medical_history set default '[]';

update public.user_health_profiles
set
  selected_ai_persona = coalesce(nullif(selected_ai_persona, ''), 'default'),
  allergies = coalesce(nullif(allergies, ''), '[]'),
  injury_history = coalesce(nullif(injury_history, ''), '[]'),
  medical_history = coalesce(nullif(medical_history, ''), '[]')
where
  selected_ai_persona is null
  or selected_ai_persona = ''
  or allergies is null
  or allergies = ''
  or injury_history is null
  or injury_history = ''
  or medical_history is null
  or medical_history = '';

create index if not exists exercise_items_exercise_id_idx
  on public.exercise_items (exercise_id);
