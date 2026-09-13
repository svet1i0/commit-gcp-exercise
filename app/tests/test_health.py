"""Unit tests for /health contract and migration configuration — no cloud mutation."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import unittest
from concurrent.futures import TimeoutError as FuturesTimeout
from http.server import ThreadingHTTPServer
from unittest import mock
from urllib.request import urlopen

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
        os.environ.pop("HEALTH_DB_TIMEOUT_SEC", None)
        os.environ.pop("HEALTH_SECRET_TIMEOUT_SEC", None)
        main.DB_TIMEOUT_SEC = 15.0
        main.SECRET_TIMEOUT_SEC = 15.0
        with main._connector_lock:
            main._connector = None
        with main._sm_lock:
            main._sm_client = None

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
        with main._sm_lock:
            main._sm_client = None
        main.DB_TIMEOUT_SEC = 15.0
        main.SECRET_TIMEOUT_SEC = 15.0

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

    def test_db_timeout(self) -> None:
        barrier = threading.Barrier(2)

        def slow_db(_deadline: float | None = None) -> str:
            barrier.wait(timeout=1)
            time.sleep(0.2)
            return "ok"

        def fast_secret(_deadline: float | None = None) -> str:
            barrier.wait(timeout=1)
            return "ok"

        os.environ["HEALTH_DB_TIMEOUT_SEC"] = "0.05"
        os.environ["HEALTH_SECRET_TIMEOUT_SEC"] = "2"
        main.DB_TIMEOUT_SEC = 0.05
        main.SECRET_TIMEOUT_SEC = 2.0
        with mock.patch.object(main, "check_database", side_effect=slow_db), mock.patch.object(
            main, "check_secrets", side_effect=fast_secret
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "error")
        self.assertEqual(body["secret"], "ok")

    def test_secret_timeout(self) -> None:
        barrier = threading.Barrier(2)

        def fast_db(_deadline: float | None = None) -> str:
            barrier.wait(timeout=1)
            return "ok"

        def slow_secret(_deadline: float | None = None) -> str:
            barrier.wait(timeout=1)
            time.sleep(0.2)
            return "ok"

        main.DB_TIMEOUT_SEC = 2.0
        main.SECRET_TIMEOUT_SEC = 0.05
        with mock.patch.object(main, "check_database", side_effect=fast_db), mock.patch.object(
            main, "check_secrets", side_effect=slow_secret
        ):
            code, body = main.build_health()
        self.assertEqual(code, 503)
        self.assertEqual(body["db"], "ok")
        self.assertEqual(body["secret"], "error")

    def test_both_checks_started_before_await(self) -> None:
        order: list[str] = []
        started = threading.Event()
        release = threading.Event()

        def db(_deadline: float | None = None) -> str:
            order.append("db_start")
            started.set()
            release.wait(timeout=1)
            order.append("db_end")
            return "ok"

        def secret(_deadline: float | None = None) -> str:
            order.append("secret_start")
            started.wait(timeout=1)
            release.set()
            order.append("secret_end")
            return "ok"

        with mock.patch.object(main, "check_database", side_effect=db), mock.patch.object(
            main, "check_secrets", side_effect=secret
        ):
            code, body = main.build_health()
        self.assertEqual(code, 200)
        self.assertIn("db_start", order)
        self.assertIn("secret_start", order)
        # Both starts precede either end under concurrent scheduling.
        self.assertLess(order.index("db_start"), min(order.index("db_end"), order.index("secret_end")))
        self.assertLess(order.index("secret_start"), min(order.index("db_end"), order.index("secret_end")))

    def test_parallel_wall_clock_not_serial_sum(self) -> None:
        """Each check sleeps ~0.15s; serial would be ~0.30s; parallel should finish sooner."""

        def slow(_deadline: float | None = None) -> str:
            time.sleep(0.15)
            return "ok"

        main.DB_TIMEOUT_SEC = 2.0
        main.SECRET_TIMEOUT_SEC = 2.0
        with mock.patch.object(main, "check_database", side_effect=slow), mock.patch.object(
            main, "check_secrets", side_effect=slow
        ):
            t0 = time.perf_counter()
            code, body = main.build_health()
            elapsed = time.perf_counter() - t0
        self.assertEqual(code, 200)
        self.assertEqual(body["db"], "ok")
        self.assertEqual(body["secret"], "ok")
        self.assertLess(elapsed, 0.28)

    def test_two_simultaneous_health_without_starvation(self) -> None:
        gate = threading.Barrier(4)  # 2 requests × 2 checks

        def work(_deadline: float | None = None) -> str:
            gate.wait(timeout=2)
            return "ok"

        with mock.patch.object(main, "check_database", side_effect=work), mock.patch.object(
            main, "check_secrets", side_effect=work
        ):
            results: list[tuple[int, dict]] = []

            def run() -> None:
                results.append(main.build_health())

            t1 = threading.Thread(target=run)
            t2 = threading.Thread(target=run)
            t1.start()
            t2.start()
            t1.join(timeout=3)
            t2.join(timeout=3)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(code == 200 for code, _ in results))

    def test_await_future_on_timeout(self) -> None:
        fut = mock.Mock()
        fut.result.side_effect = FuturesTimeout()
        fut.cancel.return_value = True
        deadline = time.perf_counter() + 0.05
        self.assertEqual(main._await_future(fut, deadline, label="overall_db_check"), "error")
        fut.cancel.assert_called()

    def test_request_time_secret_reads_every_health(self) -> None:
        calls: list[str] = []

        def fake_access(project: str, secret_id: str, *, timeout: float) -> bytes:
            self.assertGreater(timeout, 0)
            calls.append(secret_id)
            return b"x"

        with mock.patch.object(main, "check_database", return_value="ok"), mock.patch.object(
            main, "_access_secret", side_effect=fake_access
        ):
            main.build_health()
            main.build_health()
        self.assertEqual(calls.count("meridian-db-password"), 2)
        self.assertEqual(calls.count("meridian-third-party-token"), 2)

    def test_secret_manager_rpc_timeouts_positive(self) -> None:
        seen: list[float] = []

        class FakeClient:
            def access_secret_version(self, request=None, timeout=None):  # noqa: ANN001
                seen.append(float(timeout))
                resp = mock.Mock()
                resp.payload.data = b"x"
                return resp

        with main._sm_lock:
            main._sm_client = FakeClient()
        self.assertEqual(main.check_secrets(time.perf_counter() + 5), "ok")
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(t > 0 for t in seen))
        # Second call has less remaining budget than the first.
        self.assertLessEqual(seen[1], seen[0])

    def test_sm_client_reused_payloads_not_cached(self) -> None:
        payloads = [b"one", b"two", b"three", b"four"]

        class FakeClient:
            def __init__(self) -> None:
                self.n = 0

            def access_secret_version(self, request=None, timeout=None):  # noqa: ANN001
                resp = mock.Mock()
                resp.payload.data = payloads[self.n]
                self.n += 1
                return resp

        client = FakeClient()
        with main._sm_lock:
            main._sm_client = client
        self.assertEqual(main.check_secrets(time.perf_counter() + 5), "ok")
        self.assertEqual(main.check_secrets(time.perf_counter() + 5), "ok")
        self.assertEqual(client.n, 4)
        with main._sm_lock:
            self.assertIs(main._sm_client, client)

    def test_connector_process_scoped_conn_request_scoped(self) -> None:
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
            self.assertEqual(main.check_database(time.perf_counter() + 5), "ok")
            self.assertEqual(main.check_database(time.perf_counter() + 5), "ok")
        self.assertEqual(get_c.call_count, 2)
        self.assertEqual(fake_connector.connect.call_count, 2)
        self.assertEqual(fake_conn.close.call_count, 2)

    def test_cursor_and_conn_close_on_query_failure(self) -> None:
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
            self.assertEqual(main.check_database(time.perf_counter() + 5), "error")
        fake_cur.close.assert_called()
        fake_conn.close.assert_called_once()

    def test_failures_do_not_expose_messages_or_payloads(self) -> None:
        def boom(_deadline: float | None = None) -> str:
            raise RuntimeError("super-secret-connection-string://user:pass@host/db")

        with mock.patch.object(main, "check_database", side_effect=boom), mock.patch.object(
            main, "check_secrets", return_value="ok"
        ):
            code, body = main.build_health()
        dumped = json.dumps(body)
        self.assertNotIn("super-secret", dumped)
        self.assertNotIn("connection-string", dumped)
        self.assertEqual(set(body.keys()), {"candidate", "commit", "region", "db", "secret"})
        self.assertEqual(code, 503)

    def test_structured_logs_include_stage_outcome_elapsed(self) -> None:
        records: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        h = Capture()
        main.log.addHandler(h)
        try:
            with mock.patch.object(main, "_access_secret", return_value=b"pw"), mock.patch.object(
                main, "_get_connector"
            ) as get_c:
                get_c.side_effect = RuntimeError("boom")
                with mock.patch.dict(
                    "sys.modules",
                    {"google.cloud.sql.connector": mock.MagicMock(IPTypes=mock.Mock(PRIVATE="PRIVATE"))},
                ):
                    main.check_database(time.perf_counter() + 5)
        finally:
            main.log.removeHandler(h)

        joined = "\n".join(records)
        self.assertNotIn("pw", joined)  # payload itself shouldn't appear; password bytes not logged
        self.assertIn("health_diag", joined)
        self.assertIn("exception_class", joined)
        self.assertIn("elapsed_ms", joined)
        self.assertIn("outcome", joined)

    def test_non_health_route_404(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), main.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urlopen(f"http://{host}:{port}/nope") as resp:  # noqa: S310
                self.fail(f"expected 404, got {resp.status}")
        except Exception as exc:  # noqa: BLE001
            self.assertIn("404", str(exc))
        finally:
            server.shutdown()

    def test_secret_resource_uses_version_1(self) -> None:
        name = main._secret_resource("meridian-poc-ss-260913", "meridian-db-password")
        self.assertEqual(
            name,
            "projects/meridian-poc-ss-260913/secrets/meridian-db-password/versions/1",
        )

    def test_check_secrets_reads_both_secrets(self) -> None:
        calls: list[str] = []

        def fake_access(project: str, secret_id: str, *, timeout: float) -> bytes:
            calls.append(secret_id)
            return b"x"

        with mock.patch.object(main, "_access_secret", side_effect=fake_access):
            self.assertEqual(main.check_secrets(time.perf_counter() + 5), "ok")
        self.assertEqual(calls, ["meridian-db-password", "meridian-third-party-token"])

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
