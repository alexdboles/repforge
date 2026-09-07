"""Criterion: End Simulation is a hard stop even mid-generation.

Repro: start a simulation, fire a turn (rep line), then ~0.5s later fire two
concurrent /complete calls. Exactly one /complete must return 200 with an
evaluation, the other 409. The in-flight /turns call must return 409 and its
prospect reply must be absent from the final transcript, while the rep's line
IS present. Final status must be 'completed'.
"""

import asyncio

import httpx
import pytest

from .conftest import API_URL, activate_sim, signup_user

TIMEOUT = 180.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-end-hardstop-rep", timeout=TIMEOUT)
    yield c, user_id
    c.close()


@pytest.mark.asyncio
async def test_end_simulation_hard_stop_mid_turn(rep_user):
    c, user_id = rep_user
    start = c.post(
        "/simulations",
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

    async with httpx.AsyncClient(
        base_url=API_URL, timeout=TIMEOUT, headers=dict(c.headers)
    ) as ac:
        turn_task = asyncio.create_task(
            ac.post(
                f"/simulations/{sim_id}/turns",
                json={"text": "Hi, do you have a minute to talk about your CRM?", "at": 1.0},
            )
        )
        await asyncio.sleep(0.5)
        complete_task_1 = asyncio.create_task(ac.post(f"/simulations/{sim_id}/complete"))
        complete_task_2 = asyncio.create_task(ac.post(f"/simulations/{sim_id}/complete"))

        turn_resp, c1, c2 = await asyncio.gather(turn_task, complete_task_1, complete_task_2)

    complete_statuses = sorted([c1.status_code, c2.status_code])
    assert complete_statuses == [200, 409], (c1.status_code, c1.text, c2.status_code, c2.text)
    winner = c1 if c1.status_code == 200 else c2
    winner_body = winner.json()
    assert winner_body["status"] == "completed", winner_body

    # The in-flight turns call must see the call already ended.
    assert turn_resp.status_code == 409, turn_resp.text

    final = c.get(f"/simulations/{sim_id}")
    assert final.status_code == 200, final.text
    final_body = final.json()
    assert final_body["status"] == "completed"
    transcript = final_body["transcript"]
    rep_lines = [t for t in transcript if t["speaker"] == "rep"]
    prospect_lines = [t for t in transcript if t["speaker"] == "prospect"]
    assert len(rep_lines) == 1, transcript
    assert rep_lines[0]["text"].startswith("Hi, do you have a minute")
    # Only the opening prospect line (inserted at sim start) may be present —
    # the reply to the in-flight turn (which returned 409) must never have landed.
    assert len(prospect_lines) == 1, transcript
    assert prospect_lines[0]["at"] == 0.0, transcript
