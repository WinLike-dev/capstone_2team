alter table if exists public.user_health_profiles
  alter column gender set default 'unknown',
  alter column age set default 0,
  alter column height set default 0,
  alter column weight set default 0,
  alter column bmi set default 0;

update public.user_health_profiles
set
  gender = coalesce(nullif(gender, ''), 'unknown'),
  age = coalesce(age, 0),
  height = coalesce(height, 0),
  weight = coalesce(weight, 0),
  bmi = coalesce(bmi, 0)
where
  gender is null
  or gender = ''
  or age is null
  or height is null
  or weight is null
  or bmi is null;
