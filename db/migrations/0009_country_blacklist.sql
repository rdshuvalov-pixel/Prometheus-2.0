INSERT INTO reject_reasons (code, label) VALUES
  ('country_blacklisted', 'Локация в стоп-листе')
ON CONFLICT (code) DO NOTHING;
