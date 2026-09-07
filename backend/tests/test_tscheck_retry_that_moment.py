"""Criterion: Retry That Moment creates a focused retry of one coaching moment.

Full flow: complete a graded call with a weak pitch (reliably produces misses),
then POST /simulations/{id}/retry-moment {"miss_index": 0}. Verify shape, that
the retry can itself be completed/evaluated independently, that the ORIGINAL
simulation is untouched, and the negative cases (foreign id -> 404, miss_index
out of range -> 404).
"""

import httpx
import pytest

from .conftest import api_url, activate_sim, signup_user

TIMEOUT = 180.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-retry-moment-rep", timeout=TIMEOUT)
    yield c, user_id
    c.close()


@pytest.fixture
def other_user():
    c, user_id, _ = signup_user("tscheck-retry-moment-other", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def _start_and_complete_weak_call(c: httpx.Client, user_id: str) -> tuple[str, dict]:
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
    activate_sim(c, sim_id)

    turn = c.post(
        api_url(f"/simulations/{sim_id}/turns"),
        json={"text": "Our platform is cheaper and has more features.", "at": 5.0},
    )
    assert turn.status_code == 200, turn.text

    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 200, complete.text
    return sim_id, complete.json()


def test_retry_moment_full_flow_and_original_unchanged(rep_user, other_user):
    c, rep_id = rep_user
    other_c, _ = other_user

    sim_id, completed = _start_and_complete_weak_call(c, rep_id)
    original_score = completed["evaluation"]["overall_score"]
    misses = completed["evaluation"].get("misses") or []
    assert len(misses) > 0, "weak pitch should produce at least one miss to retry"

    retry = c.post(api_url(f"/simulations/{sim_id}/retry-moment"), json={"miss_index": 0})
    assert retry.status_code == 200, retry.text
    body = retry.json()

    assert body["mode"] == "moment"
    assert body["retry_of"] == sim_id
    assert body.get("moment_label")
    assert body.get("moment_situation")
    assert body.get("moment_objective")
    assert body["origin_score"] == original_score

    transcript = body["transcript"]
    prospect_lines = [t for t in transcript if t["speaker"] == "prospect"]
    assert len(prospect_lines) == 1, transcript
    assert len(transcript) == 1, transcript

    retry_id = body["id"]
    activate_sim(c, retry_id)

    # Send a typed reply and complete the retry -> gets its own evaluation.
    reply = c.post(
        api_url(f"/simulations/{retry_id}/turns"),
        json={"text": "Before I get into features, what's this being compared against on price?", "at": 4.0},
    )
    assert reply.status_code == 200, reply.text

    retry_complete = c.post(api_url(f"/simulations/{retry_id}/complete"))
    assert retry_complete.status_code == 200, retry_complete.text
    retry_done = retry_complete.json()
    assert isinstance(retry_done.get("moment_improved"), bool)

    # Original simulation must be entirely unchanged.
    original_after = c.get(api_url(f"/simulations/{sim_id}"))
    assert original_after.status_code == 200, original_after.text
    original_after_body = original_after.json()
    assert original_after_body["status"] == "completed"
    assert original_after_body["evaluation"]["overall_score"] == original_score
    assert original_after_body["transcript"] == completed["transcript"]

    # Foreign user's simulation id -> 404.
    foreign = other_c.post(api_url(f"/simulations/{sim_id}/retry-moment"), json={"miss_index": 0})
    assert foreign.status_code == 404, foreign.text

    # miss_index out of range (but schema-valid, <=20) on the graded original -> 404.
    bad_index = c.post(
        api_url(f"/simulations/{sim_id}/retry-moment"), json={"miss_index": min(len(misses) + 5, 20)}
    )
    assert bad_index.status_code == 404, bad_index.text
