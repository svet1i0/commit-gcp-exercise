"""Unit tests for /health contract — no cloud mutation."""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

# Ensure app package path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402


class HealthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["COMMIT_SHA"] = "abcdef1234567890"
        os.environ["GCP_REGION"] = "europe-west1"

    def tearDown(self) -> None:
        for k in (
            "COMMIT_SHA",
            "GCP_REGION",
            "DB_HOST",
            "DB_PASSWORD",
            "GCP_PROJECT",
            "DB_PASSWORD_SECRET",
            "THIRD_PARTY_TOKEN_SECRET",
        ):
            os.environ.pop(k, None)

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
            # _run_with_timeout swallows; direct build uses patched check_* returning via timeout wrapper
            code, body = main.build_health()
        dumped = json.dumps(body)
        self.assertNotIn("super-secret", dumped)
        self.assertNotIn("connection-string", dumped)
        self.assertEqual(set(body.keys()), {"candidate", "commit", "region", "db", "secret"})


class MigrationScriptTests(unittest.TestCase):
    def test_migration_file_exists(self) -> None:
        path = Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
        self.assertTrue(path.is_file())
        text = path.read_text()
        self.assertIn("schema_migrations", text)


if __name__ == "__main__":
    unittest.main()
