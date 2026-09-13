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
DB_TIMEOUT_SEC = float(os.environ.get("HEALTH_DB_TIMEOUT_SEC", "3"))
SECRET_TIMEOUT_SEC = float(os.environ.get("HEALTH_SECRET_TIMEOUT_SEC", "3"))


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def check_database() -> str:
    """Run a real SQL query; return 'ok' or 'error'. Never raise secret details."""
    host = _env("DB_HOST")
    port = int(_env("DB_PORT", "5432") or "5432")
    database = _env("DB_NAME", "meridian")
    user = _env("DB_USER", "app_user")
    password = _env("DB_PASSWORD")
    # Optional: password from Secret Manager resource name handled in check_secrets;
    # runtime may inject DB_PASSWORD from Cloud Run secret env or fetch in-process.
    if not host or not password:
        return "error"
    try:
        import pg8000.native  # type: ignore

        conn = pg8000.native.Connection(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            timeout=DB_TIMEOUT_SEC,
        )
        try:
            row = conn.run("SELECT 1")
            if not row or row[0][0] != 1:
                return "error"
            return "ok"
        finally:
            conn.close()
    except Exception:
        log.warning("database health check failed")
        return "error"


def check_secrets() -> str:
    """Read both required Secret Manager secret versions; return 'ok' or 'error'."""
    project = _env("GCP_PROJECT") or _env("GOOGLE_CLOUD_PROJECT")
    db_secret = _env("DB_PASSWORD_SECRET")  # projects/.../secrets/.../versions/latest
    token_secret = _env("THIRD_PARTY_TOKEN_SECRET")
    if not project or not db_secret or not token_secret:
        return "error"
    try:
        from google.cloud import secretmanager  # type: ignore

        client = secretmanager.SecretManagerServiceClient()

        def _read(name: str) -> bytes:
            # Accept full resource name or secret id
            resource = name
            if not name.startswith("projects/"):
                resource = f"projects/{project}/secrets/{name}/versions/latest"
            resp = client.access_secret_version(request={"name": resource})
            return resp.payload.data

        data1 = _read(db_secret)
        data2 = _read(token_secret)
        if not data1 or not data2:
            return "error"
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

    # Independent attempts (separate timeouts)
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
    # Bind check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.close()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    log.info("listening on :%s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
