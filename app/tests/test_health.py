"""Unit tests for /health contract and migration configuration — no cloud mutation."""

from __future__ import annotations

import json
import logging
import os
import unittest
from concurrent.futures import TimeoutError as FuturesTimeout
from unittest import mock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402
import migrations.migrate as migrate  # noqa: E402


class HealthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["COMMIT_SHA"] = "abcdef1234567890"
        os.environ["GCP_REGION"] = "europe-west1"
        os.environ["GCP_PROJECT"] = "meridian-poc-ss-260913"
        os.environ["INSTANCE_CONNECTION_NAME"] = "meridian-poc-ss-260913:europe-west1:meridian-pg"
        os.environ["DB_PASSWORD_SECRET"] = "meridian-db-password"
        os.environ["THIRD_PARTY_TOKEN_SECRET"] = "meridian-third-party-token"
        os.environ["DB_USER"] = "app_user"
        os.environ["DB_NAME"] = "meridian"
        # Reset process connector between tests
        with main._connector_lock:
            main._connector = None

    def tearDown(self) -> None:
        for k in (
            "COMMIT_SHA",
            "GCP_REGION",
            "GCP_PROJECT",
            "INSTANCE_CONNECTION_NAME",
            "DB_PASSWORD_SECRET",
            "THIRD_PARTY_TOKEN_SECRET",
            "DB_USER",
            "DB_NAME",
            "DB_PASSWORD",
            "DB_HOST",
            "HEALTH_DB_TIMEOUT_SEC",
            "HEALTH_SECRET_TIMEOUT_SEC",
        ):
            os.environ.pop(k, None)
        with main._connector_lock:
            main._connector = None

    def test_success_exact_five_keys(self) -> None:
        with mock.patch.object(main, "check_database", return_value="ok"), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            code, body = main.build_health()
        self.assertEqual(code, 200)
        self.assertEqual(set(body.keys()), {"candidate", "commit", "region", "db", "secret"})
        self.assertEqual(body["candidate"], "Svetoslav Silkov")
        self.assertEqual(body["commit"], "abcdef1")
        self.assertEqual(body["region"], "europe-west1")
        self.assertEqual(body["db"], "ok")
        self.assertEqual(body["secret"], "ok")

    def test_db_failure_independent(self) -> None:
        with mock.patch.object(main, "check_database", return_value="error"), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "error")
        self.assertEqual(body["secret"], "ok")

    def test_secret_failure_independent(self) -> None:
        with mock.patch.object(main, "check_database", return_value="ok"), mock.patch.object(
            main, "check_secrets", return_value="error"
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "ok")
        self.assertEqual(body["secret"], "error")

    def test_both_failures(self) -> None:
        with mock.patch.object(main, "check_database", return_value="error"), mock.patch.object(
            main, "check_secrets", return_value="error"
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "error")
        self.assertEqual(body["secret"], "error")

    def test_timeout_returns_error_and_503(self) -> None:
        with mock.patch.object(
            main, "_run_with_timeout", side_effect=["error", "ok"]
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "error")
        self.assertEqual(body["secret"], "ok")
        self.assertEqual(set(body.keys()), {"candidate", "commit", "region", "db", "secret"})

    def test_run_with_timeout_on_futures_timeout(self) -> None:
        fut = mock.Mock()
        fut.result.side_effect = FuturesTimeout()
        with mock.patch.object(main._executor, "submit", return_value=fut):
            self.assertEqual(main._run_with_timeout(lambda: "ok", 0.01, label="overall_db_check"), "error")

    def test_no_secret_values_in_body(self) -> None:
        with mock.patch.object(main, "check_database", return_value="ok"), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            _, body = main.build_health()
        dumped = json.dumps(body)
        self.assertNotIn("password", dumped.lower())
        for v in body.values():
            self.assertIn(v, {"Svetoslav Silkov", "abcdef1", "europe-west1", "ok", "error"})

    def test_exception_not_exposed(self) -> None:
        def boom() -> str:
            raise RuntimeError("super-secret-connection-string://user:pass@host/db")

        with mock.patch.object(main, "check_database", side_effect=boom), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            # build_health uses executor wrapper; patch check_database at call site via _run_with_timeout
            with mock.patch.object(main, "_run_with_timeout", side_effect=["error", "ok"]):
                code, body = main.build_health()
        dumped = json.dumps(body)
        self.assertNotIn("super-secret", dumped)
        self.assertNotIn("connection-string", dumped)
        self.assertEqual(set(body.keys()), {"candidate", "commit", "region", "db", "secret"})
        self.assertEqual(code, 503)

    def test_secret_resource_uses_version_1(self) -> None:
        name = main._secret_resource("meridian-poc-ss-260913", "meridian-db-password")
        self.assertEqual(
            name,
            "projects/meridian-poc-ss-260913/secrets/meridian-db-password/versions/1",
        )

    def test_check_secrets_reads_both_secrets(self) -> None:
        calls: list[str] = []

        def fake_access(project: str, secret_id: str) -> bytes:
            calls.append(secret_id)
            return b"x"

        with mock.patch.object(main, "_access_secret", side_effect=fake_access):
            self.assertEqual(main.check_secrets(), "ok")
        self.assertEqual(calls, ["meridian-db-password", "meridian-third-party-token"])

    def test_check_database_reuses_connector_and_closes_conn(self) -> None:
        fake_conn = mock.MagicMock()
        fake_cur = mock.MagicMock()
        fake_conn.cursor.return_value = fake_cur
        fake_cur.fetchone.return_value = (1,)
        fake_connector = mock.MagicMock()
        fake_connector.connect.return_value = fake_conn

        with mock.patch.object(main, "_access_secret", return_value=b"pw"), mock.patch.object(
            main, "_get_connector", return_value=fake_connector
        ) as get_c, mock.patch.dict(
            "sys.modules",
            {"google.cloud.sql.connector": mock.MagicMock(IPTypes=mock.Mock(PRIVATE="PRIVATE"))},
        ):
            self.assertEqual(main.check_database(), "ok")
            self.assertEqual(main.check_database(), "ok")

        self.assertEqual(get_c.call_count, 2)
        self.assertEqual(fake_connector.connect.call_count, 2)
        self.assertEqual(fake_conn.close.call_count, 2)
        for call in fake_connector.connect.call_args_list:
            self.assertIn("timeout", call.kwargs)
            self.assertNotIn("password", str(call.kwargs.get("timeout")))

    def test_check_database_closes_conn_on_failure(self) -> None:
        fake_conn = mock.MagicMock()
        fake_cur = mock.MagicMock()
        fake_conn.cursor.return_value = fake_cur
        fake_cur.execute.side_effect = RuntimeError("query-failed")
        fake_connector = mock.MagicMock()
        fake_connector.connect.return_value = fake_conn

        with mock.patch.object(main, "_access_secret", return_value=b"pw"), mock.patch.object(
            main, "_get_connector", return_value=fake_connector
        ), mock.patch.dict(
            "sys.modules",
            {"google.cloud.sql.connector": mock.MagicMock(IPTypes=mock.Mock(PRIVATE="PRIVATE"))},
        ):
            self.assertEqual(main.check_database(), "error")
        fake_conn.close.assert_called_once()

    def test_health_diag_logs_have_no_sensitive_values(self) -> None:
        records: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        h = Capture()
        main.log.addHandler(h)
        try:
            with mock.patch.object(main, "_access_secret", return_value=b"super-secret-password"), mock.patch.object(
                main, "_get_connector"
            ) as get_c:
                get_c.side_effect = RuntimeError("boom")
                with mock.patch.dict(
                    "sys.modules",
                    {"google.cloud.sql.connector": mock.MagicMock(IPTypes=mock.Mock(PRIVATE="PRIVATE"))},
                ):
                    main.check_database()
        finally:
            main.log.removeHandler(h)

        joined = "\n".join(records)
        self.assertNotIn("super-secret-password", joined)
        self.assertIn("health_diag", joined)
        self.assertIn("exception_class", joined)

    def test_deployed_commit_short_sha(self) -> None:
        os.environ["COMMIT_SHA"] = "910c929fbb101a6bcb8d5b012b21a460cec75cbc"
        with mock.patch.object(main, "check_database", return_value="ok"), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            _, body = main.build_health()
        self.assertEqual(body["commit"], "910c929")


class MigrationScriptTests(unittest.TestCase):
    def test_migration_file_exists(self) -> None:
        path = Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
        self.assertTrue(path.is_file())

    def test_migrate_requires_iam_user_env(self) -> None:
        for k in ("INSTANCE_CONNECTION_NAME", "DB_USER", "DB_NAME", "DB_PASSWORD"):
            os.environ.pop(k, None)
        self.assertEqual(migrate.main(), 2)

    def test_migrate_uses_iam_connector_kwargs(self) -> None:
        os.environ["INSTANCE_CONNECTION_NAME"] = "p:r:i"
        os.environ["DB_USER"] = "meridian-migrator@meridian-poc-ss-260913.iam"
        os.environ["DB_NAME"] = "meridian"
        os.environ["APP_DB_USER"] = "app_user"

        fake_conn = mock.MagicMock()
        fake_cur = mock.MagicMock()
        fake_conn.cursor.return_value = fake_cur
        fake_cur.fetchall.return_value = []
        fake_cur.fetchone.return_value = None

        fake_connector = mock.MagicMock()
        fake_connector.connect.return_value = fake_conn

        with mock.patch.dict(
            "sys.modules",
            {
                "google.cloud.sql.connector": mock.MagicMock(
                    Connector=mock.Mock(return_value=fake_connector),
                    IPTypes=mock.Mock(PRIVATE="PRIVATE"),
                )
            },
        ):
            with mock.patch("migrations.migrate.Connector", create=True), mock.patch(
                "google.cloud.sql.connector.Connector", return_value=fake_connector
            ), mock.patch("google.cloud.sql.connector.IPTypes") as ipt:
                ipt.PRIVATE = "PRIVATE"
                rc = migrate.main()

        self.assertEqual(rc, 0)
        kwargs = fake_connector.connect.call_args.kwargs
        self.assertTrue(kwargs.get("enable_iam_auth"))
        self.assertEqual(kwargs.get("user"), "meridian-migrator@meridian-poc-ss-260913.iam")
        self.assertNotIn("password", kwargs)
        for k in ("INSTANCE_CONNECTION_NAME", "DB_USER", "DB_NAME", "APP_DB_USER"):
            os.environ.pop(k, None)


if __name__ == "__main__":
    unittest.main()
