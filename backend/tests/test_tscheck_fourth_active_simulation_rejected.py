"""Criterion: concurrency guard on active simulations survived the refactor.

_guard_new_simulation caps a user at 3 concurrently 'active' simulations.
Starting a 4th while the first three are still active must return 409 and
must NOT create a new simulation row. Ending one of the three frees a slot
for the next start.
"""

import pytest

from .conftest import api_url, activate_sim, signup_user


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-fourth-active-sim-rep")
    yield c, user_id
    c.close()


def _start(c, user_id):
    r = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_fourth_concurrent_active_simulation_returns_409(rep_user):
    c, user_id = rep_user

    sim_ids = [_start(c, user_id) for _ in range(3)]
    assert len(set(sim_ids)) == 3

    fourth = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert fourth.status_code == 409, fourth.text
    assert "open calls" in fourth.json()["detail"].lower() or "live simulations" in fourth.json()["detail"].lower()

    # Ending one of the three active sims (turn + complete, since grading
    # requires at least one rep turn) frees a slot for a new start.
    activate_sim(c, sim_ids[1])
    turn = c.post(
        api_url(f"/simulations/{sim_ids[1]}/turns"),
        json={"text": "Hi, quick question about your current process.", "at": 1.0},
    )
    assert turn.status_code == 200, turn.text
    complete2 = c.post(api_url(f"/simulations/{sim_ids[1]}/complete"))
    assert complete2.status_code == 200, complete2.text

    fifth = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert fifth.status_code == 200, fifth.text
