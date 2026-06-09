"""Unit tests for the PKCE / loopback helpers used by ``como auth login``."""

from __future__ import annotations

import base64
import hashlib
import threading
import time
import urllib.parse
import urllib.request

from como._pkce import (
    build_authorize_url,
    generate_pkce,
    redirect_uri,
    wait_for_callback,
)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def test_generate_pkce_is_valid_s256() -> None:
    verifier, challenge = generate_pkce()
    # challenge is exactly base64url(sha256(verifier)), no padding.
    assert challenge == _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    assert len(verifier) == 43  # base64url(32 bytes) with padding stripped
    assert all(c not in verifier for c in "=+/")  # RFC 7636 unreserved charset
    # Two calls are independent.
    assert generate_pkce()[0] != verifier


def test_build_authorize_url_carries_pkce_params() -> None:
    url = build_authorize_url(client_id="client_01ABC", code_challenge="CHAL", state="STATE")
    assert url.startswith("https://api.workos.com/user_management/authorize?")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["response_type"] == ["code"]
    assert q["client_id"] == ["client_01ABC"]
    assert q["code_challenge"] == ["CHAL"]
    assert q["code_challenge_method"] == ["S256"]
    assert q["state"] == ["STATE"]
    assert q["redirect_uri"] == [redirect_uri()]
    assert q["provider"] == ["authkit"]


def test_wait_for_callback_captures_code_and_ignores_strays() -> None:
    port = 8799
    holder: dict[str, object] = {}

    def run() -> None:
        holder["r"] = wait_for_callback(port=port, timeout=10.0)

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.3)  # let the loopback server bind

    # A stray request (e.g. favicon) must be ignored, not mistaken for the code.
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/favicon.ico", timeout=2)
    except Exception:
        pass

    urllib.request.urlopen(
        f"http://127.0.0.1:{port}/callback?code=THECODE&state=THESTATE", timeout=2
    ).read()
    t.join(5)

    r = holder["r"]
    assert r.code == "THECODE"  # type: ignore[attr-defined]
    assert r.state == "THESTATE"  # type: ignore[attr-defined]
    assert r.error is None  # type: ignore[attr-defined]
