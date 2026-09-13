"""Meridian POC — minimal HTTP API with /health dependency checks."""

from __future__ import annotations

import json
import logging
import os
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("meridian")

CANDIDATE = "Svetoslav Silkov"
DB_TIMEOUT_SEC = float(os.environ.get("HEALTH_DB_TIMEOUT_SEC", "5"))
SECRET_TIMEOUT_SEC = float(os.environ.get("HEALTH_SECRET_TIMEOUT_SEC", "5"))
# Explicit Secret Manager versions for request-time reads (not Cloud Run env injection).
SECRET_VERSION = "1"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _secret_resource(project: str, secret_id: str) -> str:
    if secret_id.startswith("projects/"):
        return secret_id
    return f"projects/{project}/secrets/{secret_id}/versions/{SECRET_VERSION}"


def _access_secret(project: str, secret_id: str) -> bytes:
    from google.cloud import secretmanager  # type: ignore

    client = secretmanager.SecretManagerServiceClient()
    name = _secret_resource(project, secret_id)
    resp = client.access_secret_version(request={"name": name})
    return resp.payload.data


def _connect_postgres(*, user: str, password: str | None, database: str, enable_iam_auth: bool):
    """Cloud SQL Python Connector over PRIVATE IP (TLS + authenticated path)."""
    from google.cloud.sql.connector import Connector, IPTypes  # type: ignore

    instance = _env("INSTANCE_CONNECTION_NAME")
    if not instance:
        raise RuntimeError("INSTANCE_CONNECTION_NAME required")

    connector = Connector(refresh_strategy="LAZY")
    kwargs: dict = {
        "user": user,
        "db": database,
        "ip_type": IPTypes.PRIVATE,
        "enable_iam_auth": enable_iam_auth,
    }
    if not enable_iam_auth:
        if password is None:
            raise RuntimeError("password required for built-in DB user")
        kwargs["password"] = password
    # Returns a pg8000 DB-API connection
    return connector, connector.connect(instance, "pg8000", **kwargs)


def check_database() -> str:
    """Real SQL via Connector; password from Secret Manager (request-time), not env injection."""
    project = _env("GCP_PROJECT") or _env("GOOGLE_CLOUD_PROJECT")
    database = _env("DB_NAME", "meridian")
    user = _env("DB_USER", "app_user")
    db_secret = _env("DB_PASSWORD_SECRET")
    if not project or not db_secret or not _env("INSTANCE_CONNECTION_NAME"):
        return "error"
    connector = None
    try:
        password = _access_secret(project, db_secret).decode("utf-8")
        connector, conn = _connect_postgres(
            user=user, password=password, database=database, enable_iam_auth=False
        )
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            row = cur.fetchone()
            cur.close()
            if not row or row[0] != 1:
                return "error"
            return "ok"
        finally:
            conn.close()
    except Exception:
        log.warning("database health check failed")
        return "error"
    finally:
        if connector is not None:
            try:
                connector.close()
            except Exception:
                pass


def check_secrets() -> str:
    """Request-time Secret Manager API reads for BOTH configured secrets (version 1)."""
    project = _env("GCP_PROJECT") or _env("GOOGLE_CLOUD_PROJECT")
    db_secret = _env("DB_PASSWORD_SECRET")
    token_secret = _env("THIRD_PARTY_TOKEN_SECRET")
    if not project or not db_secret or not token_secret:
        return "error"
    try:
        data1 = _access_secret(project, db_secret)
        data2 = _access_secret(project, token_secret)
        if not data1 or not data2:
            return "error"
        # Never return or log payloads
        return "ok"
    except Exception:
        log.warning("secret health check failed")
        return "error"


def _run_with_timeout(fn: Callable[[], str], timeout: float) -> str:
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(fn)
        try:
            return fut.result(timeout=timeout)
        except FuturesTimeout:
            log.warning("health check timed out")
            return "error"
        except Exception:
            return "error"


def build_health() -> tuple[int, dict[str, str]]:
    """Independently evaluate db and secret; HTTP 200 only if both ok."""
    commit = _env("COMMIT_SHA", "unknown")[:7]
    region = _env("GCP_REGION", "europe-west1")

    db_status = _run_with_timeout(check_database, DB_TIMEOUT_SEC + 0.5)
    secret_status = _run_with_timeout(check_secrets, SECRET_TIMEOUT_SEC + 0.5)

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
