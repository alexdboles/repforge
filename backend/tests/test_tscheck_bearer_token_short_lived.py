"""tscheck: bearer session token is short-lived (12h) while the cookie stays long-lived (14d).

Covers: POST /api/auth/guest returns {user, token} where the bearer JWT exp is
~12h from now, the Set-Cookie repforge_session is HttpOnly; Secure; SameSite=None
with Max-Age ~1209600 (14 days), and an authenticated call succeeds using either
the cookie or the bearer token alone.
"""
import time

import httpx
import jwt

from .conftest import api_url

EXPECTED_BEARER_HOURS = 12
EXPECTED_COOKIE_DAYS = 14
TOLERANCE_SECONDS = 15 * 60  # allow for request round-trip / clock skew


def _decode_exp(token: str) -> float:
    # Signature verification isn't the point here (no access to JWT_SECRET from
    # the test process) - we only need the unverified exp claim to check TTL.
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload["exp"]


def test_guest_bearer_token_is_twelve_hours_cookie_is_fourteen_days():
    with httpx.Client(base_url=api_url(), timeout=30.0) as c:
        resp = c.post("/auth/guest")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "user" in body and "token" in body
        token = body["token"]
        assert isinstance(token, str) and len(token) > 10

        now = time.time()
        exp = _decode_exp(token)
        hours_from_now = (exp - now) / 3600.0
        assert 12 - 0.5 <= hours_from_now <= 12 + 0.5, (
            f"bearer token exp should be ~12h from now, got {hours_from_now:.2f}h"
        )

        set_cookie = resp.headers.get("set-cookie", "")
        assert "repforge_session=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "Secure" in set_cookie
        assert "samesite=none" in set_cookie.lower()
        assert "Max-Age=1209600" in set_cookie, set_cookie

        cookie_val = resp.cookies.get("repforge_session")
        assert cookie_val
        cookie_exp = _decode_exp(cookie_val)
        cookie_days_from_now = (cookie_exp - now) / 86400.0
        assert EXPECTED_COOKIE_DAYS - 0.1 <= cookie_days_from_now <= EXPECTED_COOKIE_DAYS + 0.1, (
            f"cookie exp should be ~14d from now, got {cookie_days_from_now:.2f}d"
        )

        # Authenticated call works via the cookie alone (set manually - httpx's
        # jar won't replay a Secure cookie over plain http on localhost).
        me_via_cookie = c.get(
            "/auth/me", headers={"Cookie": f"repforge_session={cookie_val}"}
        )
        assert me_via_cookie.status_code == 200, me_via_cookie.text

        # Authenticated call also works via the bearer token alone, no cookie.
        with httpx.Client(base_url=api_url(), timeout=30.0) as bearer_only:
            me_via_bearer = bearer_only.get(
                "/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert me_via_bearer.status_code == 200, me_via_bearer.text
            assert me_via_bearer.json()["id"] == body["user"]["id"]
