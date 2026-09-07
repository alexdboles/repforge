"""Criterion: lib/llm.evaluate_conversation (EvalRequest dataclass) and
routers/insights.attempt_series (_attempt/_apply_totals/_apply_category_movement)
still produce a full graded scorecard and a correct attempts series.

Flow: complete a call -> full scorecard shape. Then complete a 2nd call on the
same exercise -> GET /users/{me}/attempts/{exercise_id} returns attempts[] with
index/overall_score/categories plus first_score/latest_score/best_score/delta
and (with 2+ attempts) category_deltas/most_improved/still_weakest.
"""

import httpx
import pytest

from .conftest import api_url, activate_sim, signup_user

TIMEOUT = 180.0

EXERCISE_ID = "cold-call"


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-attempts-rep", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def _complete_call(c: httpx.Client, user_id: str, text: str) -> dict:
    start = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": EXERCISE_ID,
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert start.status_code == 200, start.text
    sim_id = start.json()["id"]
    activate_sim(c, sim_id)

    turn = c.post(api_url(f"/simulations/{sim_id}/turns"), json={"text": text, "at": 5.0})
    assert turn.status_code == 200, turn.text

    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 200, complete.text
    return complete.json()


def test_scorecard_shape_and_attempts_series(rep_user):
    c, user_id = rep_user

    first = _complete_call(
        c, user_id, "Our platform is cheaper and has more features than what you use today."
    )
    ev = first["evaluation"]
    for key in ("overall_score", "category_scores", "strengths", "misses", "coaching_priorities", "metrics"):
        assert key in ev, f"missing {key} in evaluation: {ev.keys()}"
    assert isinstance(ev["overall_score"], (int, float))
    assert isinstance(ev["category_scores"], list) and len(ev["category_scores"]) > 0
    assert "category" in ev["category_scores"][0] and "score" in ev["category_scores"][0]

    # only one attempt so far
    attempts_resp = c.get(api_url(f"/users/{user_id}/attempts/{EXERCISE_ID}"))
    assert attempts_resp.status_code == 200, attempts_resp.text
    body1 = attempts_resp.json()
    assert len(body1["attempts"]) >= 1
    a0 = body1["attempts"][0]
    for key in ("index", "overall_score", "categories"):
        assert key in a0, f"missing {key} in attempt: {a0.keys()}"
    assert body1["first_score"] == body1["latest_score"] == body1["best_score"]
    assert body1["delta"] == 0

    second = _complete_call(
        c, user_id, "Let me ask about your current priorities before I pitch anything."
    )
    ev2 = second["evaluation"]

    attempts_resp2 = c.get(api_url(f"/users/{user_id}/attempts/{EXERCISE_ID}"))
    assert attempts_resp2.status_code == 200, attempts_resp2.text
    body2 = attempts_resp2.json()
    assert len(body2["attempts"]) >= 2

    assert body2["first_score"] == ev["overall_score"]
    assert body2["latest_score"] == ev2["overall_score"]
    assert body2["best_score"] == max(ev["overall_score"], ev2["overall_score"])
    assert body2["delta"] == body2["latest_score"] - body2["first_score"]

    # with 2+ attempts, movement fields must appear
    for key in ("category_deltas", "most_improved", "still_weakest"):
        assert key in body2, f"missing {key} in 2-attempt response: {body2.keys()}"
