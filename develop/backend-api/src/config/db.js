const { createClient } = require('@supabase/supabase-js');

// Supabase 클라이언트 인스턴스를 하나만 생성하여 애플리케이션 전체에서 재사용합니다.
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

module.exports = supabase;
