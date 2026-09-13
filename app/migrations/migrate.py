#!/usr/bin/env python3
"""Apply versioned SQL migrations via Cloud SQL Connector + IAM DB auth.

Uses meridian-migrator GCP SA as a distinct PostgreSQL IAM identity
(no password / no third Secret Manager secret).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def main() -> int:
    instance = env("INSTANCE_CONNECTION_NAME")
    database = env("DB_NAME", "meridian")
    # PostgreSQL IAM SA username: email without ".gserviceaccount.com"
    user = env("DB_USER")
    app_grant_user = env("APP_DB_USER", "app_user")
    if not all([instance, user, database]):
        print(
            "missing DB connection environment "
            "(INSTANCE_CONNECTION_NAME, DB_USER, DB_NAME)",
            file=sys.stderr,
        )
        return 2

    migrations_dir = Path(__file__).resolve().parent
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("no migrations found")
        return 0

    from google.cloud.sql.connector import Connector, IPTypes  # type: ignore

    connector = Connector(refresh_strategy="LAZY")
    try:
        conn = connector.connect(
            instance,
            "pg8000",
            user=user,
            db=database,
            ip_type=IPTypes.PRIVATE,
            enable_iam_auth=True,
        )
    except Exception as exc:
        print(f"connector connect failed: {type(exc).__name__}", file=sys.stderr)
        connector.close()
        return 1

    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()
        cur.execute("SELECT version FROM schema_migrations")
        applied = {r[0] for r in cur.fetchall()}
        for path in files:
            version = path.name
            if version in applied:
                print(f"skip {version}")
                continue
            sql = path.read_text(encoding="utf-8")
            cur.execute("SELECT pg_advisory_lock(%s)", (8675309,))
            try:
                cur.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = %s", (version,)
                )
                if cur.fetchone():
                    print(f"skip {version} (race)")
                    continue
                cur.execute(sql)
                # Runtime app uses built-in app_user — grant least privilege, not ownership transfer.
                cur.execute(
                    f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{app_grant_user}"'
                )
                cur.execute(
                    f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{app_grant_user}"'
                )
                cur.execute(
                    "INSERT INTO schema_migrations(version) VALUES (%s)", (version,)
                )
                conn.commit()
                print(f"applied {version}")
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (8675309,))
                conn.commit()
        cur.close()
        print("migrations complete")
        return 0
    except Exception as exc:
        print(f"migration failed: {type(exc).__name__}", file=sys.stderr)
        try:
            conn.rollback()
        except Exception:
            pass
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass
        connector.close()


if __name__ == "__main__":
    raise SystemExit(main())
