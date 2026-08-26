"""Criterion: Hidden scenario intel is not exposed while the call is live.

GET /api/simulations/{id} for an active simulation must not contain 'hidden' or
'personality' keys in scenario; after /complete both must be present.
"""

import pytest

from .conftest import api_url, signup_user

TIMEOUT = 180.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-hidden-intel-rep", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def test_hidden_intel_hidden_while_active_then_revealed_after_complete(rep_user):
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
    sim = start.json()
    sim_id = sim["id"]
    assert "hidden" not in sim["scenario"], sim["scenario"].keys()
    assert "personality" not in sim["scenario"], sim["scenario"].keys()

    get_active = c.get(api_url(f"/simulations/{sim_id}"))
    assert get_active.status_code == 200, get_active.text
    active_scenario = get_active.json()["scenario"]
    assert "hidden" not in active_scenario, active_scenario.keys()
    assert "personality" not in active_scenario, active_scenario.keys()

    turn = c.post(
        api_url(f"/simulations/{sim_id}/turns"),
        json={"text": "Hi Jordan, thanks for taking my call, do you have a minute?", "at": 5.0},
    )
    assert turn.status_code == 200, turn.text

    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 200, complete.text

    get_done = c.get(api_url(f"/simulations/{sim_id}"))
    assert get_done.status_code == 200, get_done.text
    done_scenario = get_done.json()["scenario"]
    assert "hidden" in done_scenario, done_scenario.keys()
    assert "personality" in done_scenario, done_scenario.keys()
