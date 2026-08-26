"""Pre-scaffolded pytest fixtures for the FastAPI backend.

Tests hit the live uvicorn process managed by supervisor (not an in-process ASGI app), so
the app under test is the same one the frontend and Playwright see. Do NOT re-create this
file — add app-specific fixtures below the marker at the bottom.
"""

import os

import httpx
import pytest
import pytest_asyncio

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API_URL = f"{BACKEND_URL}/api"


def api_url(path: str = "") -> str:
    """Absolute URL for an /api route: api_url("/status") -> http://localhost:8001/api/status."""
    return f"{API_URL}{path}"


@pytest.fixture(scope="session")
def backend_url() -> str:
    return BACKEND_URL


@pytest.fixture
def client():
    """Sync httpx client rooted at /api — the default for endpoint tests.

    Example:
        def test_status(client):
            assert client.get("/status").status_code == 200
    """
    with httpx.Client(base_url=API_URL, timeout=30.0) as c:
        yield c


@pytest_asyncio.fixture
async def aclient():
    """Async variant, for tests that also await motor/backend helpers directly."""
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as c:
        yield c


# --- app-specific fixtures below this line ---

import uuid


def signup_user(name_prefix: str, timeout: float = 60.0) -> tuple[httpx.Client, str, str]:
    """Sign up a fresh tscheck user and return (client, user_id, token).

    The client carries both the session cookie (set by the server) and an
    Authorization bearer header, matching the dual auth scheme described in
    the briefing (cookie + bearer fallback).
    """
    email = f"{name_prefix}-{uuid.uuid4().hex[:10]}@example.com"
    c = httpx.Client(base_url=API_URL, timeout=timeout)
    r = c.post(
        "/auth/signup",
        json={"name": name_prefix, "email": email, "password": "Practice2026!"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    user_id = body["user"]["id"]
    token = body["token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c, user_id, token
