"""Meridian POC — minimal HTTP API with /health dependency checks."""

from __future__ import annotations

import atexit
import json
import logging
import os
import socket
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FuturesTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("meridian")

CANDIDATE = "Svetoslav Silkov"
# Per-dependency budgets share a common request start so wall time ≈ max(budgets), not sum.
DB_TIMEOUT_SEC = float(os.environ.get("HEALTH_DB_TIMEOUT_SEC", "15"))
SECRET_TIMEOUT_SEC = float(os.environ.get("HEALTH_SECRET_TIMEOUT_SEC", "15"))
SECRET_VERSION = "1"

_connector_lock = threading.Lock()
_connector: Any | None = None
_sm_lock = threading.Lock()
_sm_client: Any | None = None
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="health")
_executor_closed = False


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _log_health(event: str, *, stage: str, elapsed_ms: float, outcome: str, **extra: Any) -> None:
    """Structured privacy-safe diagnostics (never log secrets/payloads/messages)."""
    payload = {
        "event": event,
        "stage": stage,
        "elapsed_ms": max(0, int(elapsed_ms)),
        "timeout_sec": extra.pop("timeout_sec", None),
        "exception_class": extra.pop("exception_class", None),
        "outcome": outcome,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    payload.update(extra)
    log.info("health_diag %s", json.dumps(payload, separators=(",", ":")))


def _remaining(deadline: float) -> float:
    return max(0.0, deadline - time.perf_counter())


def _secret_resource(project: str, secret_id: str) -> str:
    if secret_id.startswith("projects/"):
        return secret_id
    return f"projects/{project}/secrets/{secret_id}/versions/{SECRET_VERSION}"


def _get_sm_client() -> Any:
    """Process-scoped Secret Manager client (never caches payloads)."""
    global _sm_client
    with _sm_lock:
        if _sm_client is None:
            from google.cloud import secretmanager  # type: ignore

            t0 = time.perf_counter()
            _sm_client = secretmanager.SecretManagerServiceClient()
            _log_health(
                "secret_client",
                stage="secret_client_initialization",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                outcome="ok",
            )
        return _sm_client


def _access_secret(project: str, secret_id: str, *, timeout: float) -> bytes:
    """Request-time Secret Manager read with an explicit positive RPC timeout."""
    if timeout <= 0:
        raise TimeoutError("secret_rpc_budget_exhausted")
    client = _get_sm_client()
    name = _secret_resource(project, secret_id)
    t0 = time.perf_counter()
    resp = client.access_secret_version(request={"name": name}, timeout=timeout)
    _log_health(
        "secret_rpc",
        stage="access_secret_version",
        elapsed_ms=(time.perf_counter() - t0) * 1000,
        outcome="ok",
        timeout_sec=timeout,
    )
    return resp.payload.data


def _get_connector() -> Any:
    """Process-scoped Cloud SQL Connector (lazy refresh for Cloud Run)."""
    global _connector
    with _connector_lock:
        if _connector is None:
            from google.cloud.sql.connector import Connector  # type: ignore

            timeout = max(1, int(DB_TIMEOUT_SEC))
            t0 = time.perf_counter()
            _connector = Connector(refresh_strategy="lazy", timeout=timeout)
            _log_health(
                "connector",
                stage="connector_initialization",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                outcome="ok",
                timeout_sec=timeout,
            )
        return _connector


def _shutdown_resources() -> None:
    global _connector, _sm_client, _executor_closed
    with _connector_lock:
        if _connector is not None:
            try:
                t0 = time.perf_counter()
                _connector.close()
                _log_health(
                    "connector",
                    stage="connector_close",
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                    outcome="ok",
                )
            except Exception as exc:  # noqa: BLE001
                _log_health(
                    "connector",
                    stage="connector_close",
                    elapsed_ms=0,
                    outcome="error",
                    exception_class=type(exc).__name__,
                )
            _connector = None
    with _sm_lock:
        client = _sm_client
        _sm_client = None
    if client is not None:
        close = getattr(client, "transport", None)
        # Best-effort close when the client exposes a transport close.
        try:
            if close is not None and hasattr(close, "close"):
                close.close()
        except Exception as exc:  # noqa: BLE001
            _log_health(
                "secret_client",
                stage="secret_client_close",
                elapsed_ms=0,
                outcome="error",
                exception_class=type(exc).__name__,
            )
    if not _executor_closed:
        _executor_closed = True
        _executor.shutdown(wait=False, cancel_futures=False)


atexit.register(_shutdown_resources)


def _connect_postgres(
    *,
    user: str,
    password: str | None,
    database: str,
    enable_iam_auth: bool,
    deadline: float,
):
    """Open a short-lived DB connection via the process-scoped Connector (PRIVATE IP)."""
    from google.cloud.sql.connector import IPTypes  # type: ignore

    instance = _env("INSTANCE_CONNECTION_NAME")
    if not instance:
        raise RuntimeError("INSTANCE_CONNECTION_NAME required")

    rem = _remaining(deadline)
    if rem <= 0:
        raise TimeoutError("db_connect_budget_exhausted")

    t0 = time.perf_counter()
    connector = _get_connector()
    _log_health(
        "db_check",
        stage="connector_acquisition",
        elapsed_ms=(time.perf_counter() - t0) * 1000,
        outcome="ok",
    )

    connect_timeout = max(1, int(rem))
    kwargs: dict = {
        "user": user,
        "db": database,
        "ip_type": IPTypes.PRIVATE,
        "enable_iam_auth": enable_iam_auth,
        "timeout": connect_timeout,
    }
    if not enable_iam_auth:
        if password is None:
            raise RuntimeError("password required for built-in DB user")
        kwargs["password"] = password

    t1 = time.perf_counter()
    conn = connector.connect(instance, "pg8000", **kwargs)
    _log_health(
        "db_check",
        stage="database_connect",
        elapsed_ms=(time.perf_counter() - t1) * 1000,
        outcome="ok",
        timeout_sec=connect_timeout,
    )
    return conn


def check_database(deadline: float | None = None) -> str:
    """Real SQL via process-scoped Connector; password from Secret Manager (request-time)."""
    overall_t0 = time.perf_counter()
    if deadline is None:
        deadline = overall_t0 + DB_TIMEOUT_SEC
    project = _env("GCP_PROJECT") or _env("GOOGLE_CLOUD_PROJECT")
    database = _env("DB_NAME", "meridian")
    user = _env("DB_USER", "app_user")
    db_secret = _env("DB_PASSWORD_SECRET")
    if not project or not db_secret or not _env("INSTANCE_CONNECTION_NAME"):
        _log_health(
            "db_check",
            stage="overall_db_check",
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="error",
            exception_class="MissingConfig",
        )
        return "error"

    conn = None
    stage = "overall_db_check"
    try:
        stage = "db_password_read"
        rem = _remaining(deadline)
        if rem <= 0:
            raise TimeoutError("db_password_budget_exhausted")
        t0 = time.perf_counter()
        password = _access_secret(project, db_secret, timeout=rem).decode("utf-8")
        _log_health(
            "db_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
            outcome="ok",
            timeout_sec=rem,
        )

        stage = "database_connect"
        conn = _connect_postgres(
            user=user,
            password=password,
            database=database,
            enable_iam_auth=False,
            deadline=deadline,
        )

        stage = "select_1"
        if _remaining(deadline) <= 0:
            raise TimeoutError("select_1_budget_exhausted")
        t1 = time.perf_counter()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1")
            row = cur.fetchone()
        finally:
            cur.close()
        _log_health(
            "db_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - t1) * 1000,
            outcome="ok",
        )
        if not row or row[0] != 1:
            _log_health(
                "db_check",
                stage="overall_db_check",
                elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
                outcome="error",
                exception_class="UnexpectedQueryResult",
            )
            return "error"

        _log_health(
            "db_check",
            stage="overall_db_check",
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="ok",
            timeout_sec=DB_TIMEOUT_SEC,
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        _log_health(
            "db_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="error",
            exception_class=type(exc).__name__,
            timeout_sec=DB_TIMEOUT_SEC,
        )
        return "error"
    finally:
        if conn is not None:
            try:
                t2 = time.perf_counter()
                conn.close()
                _log_health(
                    "db_check",
                    stage="connection_close",
                    elapsed_ms=(time.perf_counter() - t2) * 1000,
                    outcome="ok",
                )
            except Exception as exc:  # noqa: BLE001
                _log_health(
                    "db_check",
                    stage="connection_close",
                    elapsed_ms=0,
                    outcome="error",
                    exception_class=type(exc).__name__,
                )


def check_secrets(deadline: float | None = None) -> str:
    """Request-time Secret Manager API reads for BOTH configured secrets (version 1)."""
    overall_t0 = time.perf_counter()
    if deadline is None:
        deadline = overall_t0 + SECRET_TIMEOUT_SEC
    project = _env("GCP_PROJECT") or _env("GOOGLE_CLOUD_PROJECT")
    db_secret = _env("DB_PASSWORD_SECRET")
    token_secret = _env("THIRD_PARTY_TOKEN_SECRET")
    if not project or not db_secret or not token_secret:
        _log_health(
            "secret_check",
            stage="overall_secret_check",
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="error",
            exception_class="MissingConfig",
        )
        return "error"
    stage = "secret_read_db_password"
    try:
        rem = _remaining(deadline)
        if rem <= 0:
            raise TimeoutError("secret_check_budget_exhausted")
        t0 = time.perf_counter()
        data1 = _access_secret(project, db_secret, timeout=rem)
        _log_health(
            "secret_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
            outcome="ok",
            timeout_sec=rem,
        )

        stage = "secret_read_third_party_token"
        rem = _remaining(deadline)
        if rem <= 0:
            raise TimeoutError("secret_check_budget_exhausted")
        t1 = time.perf_counter()
        data2 = _access_secret(project, token_secret, timeout=rem)
        _log_health(
            "secret_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - t1) * 1000,
            outcome="ok",
            timeout_sec=rem,
        )
        if not data1 or not data2:
            _log_health(
                "secret_check",
                stage="overall_secret_check",
                elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
                outcome="error",
                exception_class="EmptySecretPayload",
            )
            return "error"
        _log_health(
            "secret_check",
            stage="overall_secret_check",
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="ok",
            timeout_sec=SECRET_TIMEOUT_SEC,
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        _log_health(
            "secret_check",
            stage=stage,
            elapsed_ms=(time.perf_counter() - overall_t0) * 1000,
            outcome="error",
            exception_class=type(exc).__name__,
            timeout_sec=SECRET_TIMEOUT_SEC,
        )
        return "error"


def _submit_health_check(fn, deadline: float) -> Future:
    """Submit a check; stamp completion time so late 'ok' cannot pass after deadline."""

    def run() -> tuple[str, float]:
        try:
            status = fn(deadline)
        except Exception:  # noqa: BLE001
            status = "error"
        return status, time.perf_counter()

    return _executor.submit(run)


def _await_future(fut: Future, deadline: float, *, label: str) -> str:
    """Await a stamped check result.

    An on-time completion remains valid when retrieved after the waiter’s remaining
    budget (e.g. after awaiting the sibling check). A result that actually completed
    after its deadline is never accepted as ok. cancel() only affects queued work —
    it does not terminate an already-running worker thread.
    """
    rem = _remaining(deadline)
    t0 = time.perf_counter()
    try:
        if fut.done():
            status, completed_at = fut.result(timeout=0)
        elif rem <= 0:
            fut.cancel()
            _log_health(
                "health_timeout",
                stage=label,
                elapsed_ms=0,
                outcome="error",
                exception_class="TimeoutError",
                timeout_sec=0,
            )
            return "error"
        else:
            status, completed_at = fut.result(timeout=rem)
    except FuturesTimeout:
        fut.cancel()
        _log_health(
            "health_timeout",
            stage=label,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
            outcome="error",
            exception_class="TimeoutError",
            timeout_sec=rem,
        )
        return "error"
    except Exception as exc:  # noqa: BLE001
        _log_health(
            "health_timeout",
            stage=label,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
            outcome="error",
            exception_class=type(exc).__name__,
        )
        return "error"

    if completed_at > deadline:
        _log_health(
            "health_timeout",
            stage=label,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
            outcome="error",
            exception_class="TimeoutError",
            timeout_sec=0,
        )
        return "error"
    if status not in ("ok", "error"):
        return "error"
    return status


def build_health() -> tuple[int, dict[str, str]]:
    """Start DB and secret checks concurrently; HTTP 200 only if both ok."""
    commit = _env("COMMIT_SHA", "unknown")[:7]
    region = _env("GCP_REGION", "europe-west1")
    start = time.perf_counter()
    db_deadline = start + DB_TIMEOUT_SEC
    secret_deadline = start + SECRET_TIMEOUT_SEC

    # Submit both before awaiting either (do not nest executor submissions inside workers).
    db_fut = _submit_health_check(check_database, db_deadline)
    secret_fut = _submit_health_check(check_secrets, secret_deadline)

    db_status = _await_future(db_fut, db_deadline, label="overall_db_check")
    secret_status = _await_future(secret_fut, secret_deadline, label="secret_check")

    body = {
        "candidate": CANDIDATE,
        "commit": commit,
        "region": region,
        "db": db_status,
        "secret": secret_status,
    }
    status = 200 if db_status == "ok" and secret_status == "ok" else 503
    return status, body


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        log.info("%s - %s", self.address_string(), fmt % args)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/health":
            self._json(404, {"error": "not_found"})
            return
        code, body = build_health()
        self._json(code, body)

    def _json(self, code: int, body: dict) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    port = int(_env("PORT", "8080") or "8080")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.close()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    log.info("listening on :%s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
