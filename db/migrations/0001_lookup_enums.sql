-- Lookup tables for canonical reject reasons and warnings (prometei_filter_model §20–21)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS reject_reasons (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warnings (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

INSERT INTO reject_reasons (code, label) VALUES
  ('not_product_role', 'Не продуктовая роль'),
  ('project_manager_only', 'Только Project Manager без product ownership'),
  ('marketing_role', 'Marketing'),
  ('operations_role', 'Operations'),
  ('business_analyst_no_product', 'BA без продуктовой ответственности'),
  ('office_only', 'Только офис'),
  ('hybrid_outside_lisbon', 'Hybrid не в Лиссабоне'),
  ('us_only', 'Только США'),
  ('uk_only_without_work_rights', 'UK без права работы'),
  ('expired_or_old', 'Устарела / >5 дней'),
  ('part_time', 'Не full-time'),
  ('internship', 'Стажировка'),
  ('duplicate', 'Дубликат'),
  ('insufficient_data', 'Недостаточно данных'),
  ('low_salary', 'Низкая компенсация'),
  ('domain_mismatch', 'Домен не подходит'),
  ('below_threshold', 'Ниже порога скоринга (<50)'),
  ('search_role_excluded', 'Исключено на этапе поиска по роли')
ON CONFLICT (code) DO NOTHING;

INSERT INTO warnings (code, label) VALUES
  ('date_unknown', 'Дата публикации неизвестна'),
  ('employment_type_unknown', 'Тип занятости не указан'),
  ('salary_unknown', 'Зарплата не указана'),
  ('location_ambiguous', 'Локация неоднозначна'),
  ('remote_policy_ambiguous', 'Remote-политика неясна'),
  ('short_description', 'Короткое описание JD'),
  ('domain_risk', 'Риск домена'),
  ('seniority_too_high', 'Грейд выше профиля'),
  ('seniority_too_low', 'Грейд ниже профиля'),
  ('requires_travel', 'Требуются поездки'),
  ('requires_local_language', 'Локальный язык обязателен')
ON CONFLICT (code) DO NOTHING;
