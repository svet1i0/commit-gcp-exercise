#!/usr/bin/env python3
"""Apply versioned SQL migrations. Safe to re-run (records applied versions)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pg8000.native


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def main() -> int:
    host = env("DB_HOST")
    port = int(env("DB_PORT", "5432") or "5432")
    database = env("DB_NAME", "meridian")
    # POC Design B: single SQL user (app_user). Require explicit DB_USER — never
    # default to a fake "migrator" SQL identity.
    user = env("DB_USER")
    password = env("DB_PASSWORD")
    if not all([host, password, user, database]):
        print("missing DB connection environment (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)", file=sys.stderr)
        return 2

    migrations_dir = Path(__file__).resolve().parent
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("no migrations found")
        return 0

    conn = pg8000.native.Connection(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
        timeout=30,
    )
    try:
        conn.run(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        applied = {r[0] for r in conn.run("SELECT version FROM schema_migrations")}
        for path in files:
            version = path.name
            if version in applied:
                print(f"skip {version}")
                continue
            sql = path.read_text(encoding="utf-8")
            # advisory lock to reduce concurrent double-apply risk
            conn.run("SELECT pg_advisory_lock(8675309)")
            try:
                still = conn.run(
                    "SELECT 1 FROM schema_migrations WHERE version = :v",
                    v=version,
                )
                if still:
                    print(f"skip {version} (race)")
                    continue
                conn.run(sql)
                conn.run(
                    "INSERT INTO schema_migrations(version) VALUES (:v)",
                    v=version,
                )
                print(f"applied {version}")
            finally:
                conn.run("SELECT pg_advisory_unlock(8675309)")
        print("migrations complete")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
