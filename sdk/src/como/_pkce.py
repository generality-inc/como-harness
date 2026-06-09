"""OAuth 2.0 Authorization Code + PKCE helpers for ``como auth login``.

WorkOS AuthKit's native CLI flow: generate a ``code_verifier``/``code_challenge``
(S256), open the browser to the authorize URL, capture the ``code`` on a
``127.0.0.1`` loopback, then exchange it (with the verifier) for WorkOS access +
refresh tokens. The crypto, URL builder, and loopback capture live here, free of
``httpx``/browser/WorkOS coupling, so they're unit-tested in isolation.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import secrets
import time
import urllib.parse
from dataclasses import dataclass

# WorkOS User Management base; the CLI registers `http://127.0.0.1:<PORT>/callback`
# as an allowed redirect URI in the AuthKit dashboard.
WORKOS_BASE = "https://api.workos.com"
LOOPBACK_PORT = 8765
LOOPBACK_PATH = "/callback"


def _b64url(raw: bytes) -> str:
    """Base64url, no padding (RFC 7636 §4.1)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_pkce() -> tuple[str, str]:
    """Return ``(code_verifier, code_challenge)`` for the S256 method.

    verifier  = base64url(32 random bytes)  → 43 chars, in the RFC-7636 charset.
    challenge = base64url(sha256(verifier)).
    """
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def redirect_uri(port: int = LOOPBACK_PORT) -> str:
    return f"http://127.0.0.1:{port}{LOOPBACK_PATH}"


def build_authorize_url(
    *, client_id: str, code_challenge: str, state: str, port: int = LOOPBACK_PORT, base: str = WORKOS_BASE
) -> str:
    """WorkOS User Management authorize URL for the PKCE flow."""
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri(port),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "provider": "authkit",
        }
    )
    return f"{base.rstrip('/')}/user_management/authorize?{query}"


@dataclass(frozen=True)
class CallbackResult:
    code: str | None
    state: str | None
    error: str | None = None


class _LoopbackHandler(http.server.BaseHTTPRequestHandler):
    result: CallbackResult | None = None  # set by the class on the first /callback

    def do_GET(self) -> None:  # noqa: N802 — http.server API
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != LOOPBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        type(self).result = CallbackResult(
            code=(params.get("code") or [None])[0],
            state=(params.get("state") or [None])[0],
            error=(params.get("error") or [None])[0],
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<!doctype html><meta charset=utf-8><title>como</title>"
            b"<body style='font-family:system-ui;padding:3rem'>"
            b"<h2>Signed in to como \xe2\x9c\x93</h2><p>You can close this tab and return to the terminal.</p>"
        )

    def log_message(self, *args: object) -> None:  # silence default stderr logging
        return


def wait_for_callback(*, port: int = LOOPBACK_PORT, timeout: float = 300.0) -> CallbackResult:
    """Serve ``127.0.0.1:<port>`` until the first ``/callback`` hit (ignoring
    stray requests like favicon), then return its code/state/error. Returns an
    ``error="timeout"`` result if nothing arrives within ``timeout`` seconds."""
    _LoopbackHandler.result = None
    server = http.server.HTTPServer(("127.0.0.1", port), _LoopbackHandler)
    server.timeout = 1.0  # so handle_request returns periodically to re-check the deadline
    deadline = time.monotonic() + timeout
    try:
        while _LoopbackHandler.result is None and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    return _LoopbackHandler.result or CallbackResult(code=None, state=None, error="timeout")
