"""Criterion: POST /simulations/{id}/retry-moment on a not-yet-graded (active)
simulation returns 409 (retry_moment's _pick_moment/_build_reprise refactor
must still guard against retrying an ungraded call).
"""

import httpx
import pytest

from .conftest import api_url, signup_user

TIMEOUT = 180.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-retry-active-conflict", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def test_retry_moment_on_active_simulation_is_409(rep_user):
    c, user_id = rep_user

    start = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert start.status_code == 200, start.text
    sim_id = start.json()["id"]

    # simulation is still active (not completed/graded) at this point
    retry = c.post(api_url(f"/simulations/{sim_id}/retry-moment"), json={"miss_index": 0})
    assert retry.status_code == 409, retry.text
