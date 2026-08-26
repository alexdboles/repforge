"""Criterion: Error, empty and negative states behave correctly.

- POST /api/simulations/{id}/complete with no rep turns -> 422 with readable detail.
- POST /api/simulations with unknown exercise_id -> 404.
- POST /api/simulations with difficulty 9 -> 422.
"""

import pytest

from .conftest import api_url, signup_user


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-negative-states-rep")
    yield c, user_id
    c.close()


def test_complete_with_no_rep_turns_returns_422(rep_user):
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

    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 422, complete.text
    body = complete.json()
    assert "detail" in body
    assert isinstance(body["detail"], str) and len(body["detail"]) > 0


def test_start_with_unknown_exercise_id_returns_404(rep_user):
    c, user_id = rep_user
    r = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "tscheck-not-a-real-exercise",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert r.status_code == 404, r.text


def test_start_with_invalid_difficulty_returns_422(rep_user):
    c, user_id = rep_user
    r = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 9,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert r.status_code == 422, r.text
