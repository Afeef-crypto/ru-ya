"""Smoke-check DATABASE_URL connectivity. Does not print secrets."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse


def load_database_url() -> str | None:
    env_url = __import__("os").environ.get("DATABASE_URL")
    if env_url:
        return env_url.strip().strip('"').strip("'")
    for name in (".env", ".env.local", ".env.example"):
        path = Path(name)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def encode_password(url: str) -> str:
    p = urlparse(url)
    if not p.password:
        return url
    user = quote(p.username or "", safe="")
    pw = quote(p.password, safe="")
    host = p.hostname or ""
    port = f":{p.port}" if p.port else ""
    netloc = f"{user}:{pw}@{host}{port}"
    return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))


def try_connect(dsn: str, label: str) -> bool:
    import psycopg

    try:
        with psycopg.connect(dsn, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("select version(), current_database()")
                version, db = cur.fetchone()
                cur.execute(
                    "select exists(select 1 from pg_extension where extname='vector')"
                )
                has_vector = cur.fetchone()[0]
        print(f"STATUS=ok label={label} db={db} vector={has_vector}")
        print("VERSION=" + version.split(",")[0])
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"STATUS=fail label={label} error={type(exc).__name__}: {exc}")
        return False


def main() -> int:
    url = load_database_url()
    if not url:
        print("STATUS=missing_url")
        return 2

    try:
        import psycopg  # noqa: F401
    except ImportError:
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"]
        )

    if try_connect(url, "raw"):
        return 0
    if try_connect(encode_password(url), "encoded_password"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
