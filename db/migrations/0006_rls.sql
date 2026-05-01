-- RLS: включить после создания пользователя в Supabase Auth.
-- Анонимный доступ закрыт; authenticated читают свои данные.

ALTER TABLE candidate_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE vacancies ENABLE ROW LEVEL SECURITY;
ALTER TABLE vacancy_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cover_letters ENABLE ROW LEVEL SECURITY;

-- Политики-примеры (уточните user_id в профилях после первого логина):

CREATE POLICY "profiles_select_own" ON candidate_profiles
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "profiles_update_own" ON candidate_profiles
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "vacancies_select_authenticated" ON vacancies
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "pipeline_select_authenticated" ON pipeline_runs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "events_select_authenticated" ON pipeline_events
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "letters_select_authenticated" ON cover_letters
  FOR SELECT TO authenticated USING (true);
