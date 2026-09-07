"""Criterion: no regression on the live-turn path after add_turn was split
into _guard_turn + _prospect_reply.

- 2-3 typed turns in a row: each rep line recorded exactly once, each
  followed by exactly one prospect reply.
- An empty utterance -> 422.
- A turn on an already-completed call -> 409.
"""

import pytest

from .conftest import api_url, activate_sim, signup_user

TIMEOUT = 120.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-live-turn-guard", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def _start_sim(c, user_id):
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
    activate_sim(c, r.json()["id"])
    return r.json()["id"]


def test_multiple_typed_turns_each_recorded_once(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id)

    lines = [
        "Hi, do you have a minute to talk about your CRM?",
        "We help teams cut admin time by half, does that resonate?",
        "What would it take to get 15 minutes on your calendar next week?",
    ]
    for i, line in enumerate(lines):
        r = c.post(api_url(f"/simulations/{sim_id}/turns"), json={"text": line, "at": float(i)})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body["reply"], str) and body["reply"], body

    final = c.get(api_url(f"/simulations/{sim_id}"))
    assert final.status_code == 200, final.text
    transcript = final.json()["transcript"]
    rep_lines = [t for t in transcript if t["speaker"] == "rep"]
    prospect_lines = [t for t in transcript if t["speaker"] == "prospect"]
    # Each of our 3 typed lines recorded exactly once.
    for line in lines:
        matches = [t for t in rep_lines if t["text"] == line]
        assert len(matches) == 1, (line, transcript)
    # Opening prospect line + one reply per typed turn.
    assert len(prospect_lines) == len(lines) + 1, transcript


def test_empty_utterance_returns_422(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id)
    r = c.post(api_url(f"/simulations/{sim_id}/turns"), json={"text": "   ", "at": 1.0})
    assert r.status_code == 422, r.text


def test_turn_on_completed_call_returns_409(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id)
    r = c.post(
        api_url(f"/simulations/{sim_id}/turns"),
        json={"text": "One line before ending the call.", "at": 1.0},
    )
    assert r.status_code == 200, r.text
    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 200, complete.text

    r2 = c.post(
        api_url(f"/simulations/{sim_id}/turns"),
        json={"text": "This should be rejected.", "at": 2.0},
    )
    assert r2.status_code == 409, r2.text
