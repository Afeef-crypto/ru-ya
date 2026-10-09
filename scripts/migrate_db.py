"""Apply sql/*.sql migrations to DATABASE_URL (Supabase / Postgres)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ru_ya.config import get_settings  # noqa: E402


def main() -> int:
    try:
        import psycopg
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"])
        import psycopg

    url = get_settings().database_url
    if not url:
        print("STATUS=missing_database_url")
        return 2

    sql_dir = ROOT / "sql"
    files = sorted(sql_dir.glob("*.sql"))
    preamble = "CREATE EXTENSION IF NOT EXISTS vector;\nCREATE EXTENSION IF NOT EXISTS pgcrypto;\n"

    with psycopg.connect(url, connect_timeout=20) as conn:
        conn.execute(preamble)
        for path in files:
            print(f"APPLY {path.name}")
            conn.execute(path.read_text(encoding="utf-8"))
        conn.commit()
        row = conn.execute(
            "select exists(select 1 from pg_extension where extname='vector')"
        ).fetchone()
        tables = conn.execute(
            """
            select table_name from information_schema.tables
            where table_schema='public'
            order by table_name
            """
        ).fetchall()

    print(f"STATUS=ok vector={row[0]} tables={[t[0] for t in tables]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
