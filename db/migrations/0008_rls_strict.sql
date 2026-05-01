-- Финальные RLS: только строки с привязанным user_id (после первого логина обновите профиль).
-- Service role обходит RLS.

DROP POLICY IF EXISTS "profiles_select_own" ON candidate_profiles;
DROP POLICY IF EXISTS "profiles_update_own" ON candidate_profiles;

CREATE POLICY "profiles_select_own_strict" ON candidate_profiles
  FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "profiles_update_own_strict" ON candidate_profiles
  FOR UPDATE TO authenticated USING (auth.uid() = user_id);
