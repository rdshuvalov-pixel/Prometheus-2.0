"""Применить db/migrations/*.sql к Postgres (Supabase).

Требуется прямой URI к БД (не REST): Settings → Database → Connection string → URI.
Задайте DATABASE_URL или SUPABASE_DB_URL.

По умолчанию пропускает 0008_rls_strict.sql (после первого логина).

Использование:
  pip install -e ".[migrate]"
  DATABASE_URL='postgresql://...' python -m backend.scripts.apply_migrations
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_MIGRATIONS = _REPO / "db" / "migrations"


def _ordered_files(skip_final_rls: bool) -> list[Path]:
    names = [
        "0001_lookup_enums.sql",
        "0002_candidate_profiles.sql",
        "0003_vacancies.sql",
        "0004_audit_llm.sql",
        "0005_cover_letters.sql",
        "0006_rls.sql",
        "0007_llm_cache_and_alerts.sql",
    ]
    if not skip_final_rls:
        names.append("0008_rls_strict.sql")
    out: list[Path] = []
    for n in names:
        p = _MIGRATIONS / n
        if not p.exists():
            raise FileNotFoundError(p)
        out.append(p)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-rls-strict",
        action="store_true",
        help="Включить 0008_rls_strict.sql (после привязки user_id к профилю)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Только список файлов")
    args = parser.parse_args()

    dsn = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    skip_8 = not args.include_rls_strict
    files = _ordered_files(skip_final_rls=skip_8)

    if args.dry_run:
        for p in files:
            print(p.name)
        return

    if not dsn:
        print(
            "Ошибка: задайте DATABASE_URL или SUPABASE_DB_URL "
            "(Postgres URI из Supabase → Database → Connection parameters).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import psycopg
    except ImportError:
        print("Установите: pip install -e '.[migrate]'", file=sys.stderr)
        sys.exit(1)

    for path in files:
        sql = path.read_text(encoding="utf-8")
        print(f"Applying {path.name} ...")
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql)
    print("Миграции применены.")


if __name__ == "__main__":
    main()
