"""Criterion: Cross-user access is blocked (IDOR).

Logged in as user B, requesting user A's dashboard returns 403; requesting a
simulation id owned by user A returns 404; a spoofed user_id in the
POST /api/simulations body is ignored and the created simulation belongs to
the logged-in caller.
"""

import httpx
import pytest

from .conftest import api_url, signup_user

TIMEOUT = 120.0


@pytest.fixture
def user_a():
    c, uid, _ = signup_user("tscheck-idor-user-a", timeout=TIMEOUT)
    yield c, uid
    c.close()


@pytest.fixture
def user_b():
    c, uid, _ = signup_user("tscheck-idor-user-b", timeout=TIMEOUT)
    yield c, uid
    c.close()


def test_cross_user_dashboard_returns_403(user_a, user_b):
    client_a, uid_a = user_a
    client_b, _ = user_b

    own = client_a.get(api_url(f"/users/{uid_a}/dashboard"))
    assert own.status_code == 200, own.text

    cross = client_b.get(api_url(f"/users/{uid_a}/dashboard"))
    assert cross.status_code == 403, cross.text


def test_cross_user_simulation_returns_404(user_a, user_b):
    client_a, uid_a = user_a
    client_b, _ = user_b

    start = client_a.post(
        api_url("/simulations"),
        json={
            "user_id": uid_a,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert start.status_code == 200, start.text
    sim_id = start.json()["id"]

    cross = client_b.get(api_url(f"/simulations/{sim_id}"))
    assert cross.status_code == 404, cross.text


def test_spoofed_user_id_in_start_simulation_is_ignored(user_a, user_b):
    client_a, uid_a = user_a
    _, uid_b = user_b

    start = client_a.post(
        api_url("/simulations"),
        json={
            "user_id": uid_b,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert start.status_code == 200, start.text
    sim = start.json()
    assert sim["user_id"] == uid_a, sim
    assert sim["user_id"] != uid_b, sim
