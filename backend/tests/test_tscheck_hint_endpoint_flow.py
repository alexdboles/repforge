"""Criterion: backend hint endpoint explicit-flow fix.

GET /api/simulations/{id}/hint:
- Level 1 or 2 active call -> 200 with a hint payload.
- Level 3+ call -> 409 (hints only offered on teaching difficulties).
- Another user's simulation -> 404 (ownership hidden as not-found).
- Anonymous -> 401.
"""

import pytest

from .conftest import api_url, signup_user

TIMEOUT = 120.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-hint-flow", timeout=TIMEOUT)
    yield c, user_id
    c.close()


@pytest.fixture
def other_user():
    c, user_id, _ = signup_user("tscheck-hint-flow-other", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def _start_sim(c, user_id, difficulty):
    r = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": difficulty,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_hint_level1_returns_200_payload(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id, 1)
    r = c.get(api_url(f"/simulations/{sim_id}/hint"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict) and body, body


def test_hint_level3_returns_409(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id, 3)
    r = c.get(api_url(f"/simulations/{sim_id}/hint"))
    assert r.status_code == 409, r.text


def test_hint_other_users_sim_returns_404(rep_user, other_user):
    c, user_id = rep_user
    other_c, _ = other_user
    sim_id = _start_sim(c, user_id, 1)
    r = other_c.get(api_url(f"/simulations/{sim_id}/hint"))
    assert r.status_code == 404, r.text


def test_hint_anonymous_returns_401(rep_user):
    import httpx

    c, user_id = rep_user
    sim_id = _start_sim(c, user_id, 1)
    anon = httpx.Client(base_url=api_url(""), timeout=TIMEOUT)
    r = anon.get(f"/simulations/{sim_id}/hint")
    assert r.status_code == 401, r.text
    anon.close()
