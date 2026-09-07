"""Criterion: no regression in the ElevenLabs proxy after the hardening pass.

Contract (post-hardening): POST /api/voice/speak now takes {simulation_id, turn_id?,
text?, difficulty} and only synthesizes a prospect line that is already saved verbatim
in that simulation's transcript (anti-fabrication: it can't be asked to speak arbitrary
text). GET /api/voice/cast is now platform-admin-only QA (regular reps do not need to
list/verify the raw voice cast).

- POST /api/voice/speak for the sim's own opening prospect line -> 200 audio/mpeg with
  X-Voice-Character/X-Voice-Label headers.
- Anonymous caller -> 401.
- A simulation_id that isn't the caller's -> 404 (ownership hidden as not-found).
- Text that was never actually said by the prospect -> 404 (no fabricated speech).
- /api/voice/cast rejects a non-admin rep with 403 and lists 8 voices for a
  controlled, temporarily-flagged admin account (cleaned up after the test).
"""

import httpx
import pytest

from lib.db import db

from .conftest import API_URL, api_url, activate_sim, signup_user

TIMEOUT = 60.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-voice-speak-proxy", timeout=TIMEOUT)
    yield c, user_id
    c.close()


@pytest.fixture
def other_user():
    c, user_id, _ = signup_user("tscheck-voice-speak-proxy-other", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def _start_active_sim(c, user_id):
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
    sim = activate_sim(c, r.json()["id"])
    opening_line = sim["transcript"][0]["text"]
    return sim["id"], opening_line


def test_speak_for_saved_prospect_line_returns_audio_with_headers(rep_user):
    c, user_id = rep_user
    sim_id, opening_line = _start_active_sim(c, user_id)
    r = c.post(
        api_url("/voice/speak"),
        json={"simulation_id": sim_id, "text": opening_line, "difficulty": 1},
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("audio/mpeg"), r.headers
    assert r.headers.get("x-voice-character"), r.headers
    assert r.headers.get("x-voice-label"), r.headers


def test_speak_anonymous_returns_401():
    with httpx.Client(base_url=API_URL, timeout=TIMEOUT) as c:
        r = c.post(
            "/voice/speak",
            json={"simulation_id": "does-not-matter", "text": "Hello there", "difficulty": 1},
        )
        assert r.status_code == 401, r.text


def test_speak_cross_user_simulation_returns_404(rep_user, other_user):
    c, user_id = rep_user
    other_c, _ = other_user
    sim_id, opening_line = _start_active_sim(c, user_id)
    r = other_c.post(
        api_url("/voice/speak"),
        json={"simulation_id": sim_id, "text": opening_line, "difficulty": 1},
    )
    assert r.status_code == 404, r.text


def test_speak_fabricated_text_not_in_transcript_returns_404(rep_user):
    c, user_id = rep_user
    sim_id, _opening_line = _start_active_sim(c, user_id)
    r = c.post(
        api_url("/voice/speak"),
        json={
            "simulation_id": sim_id,
            "text": "This exact sentence was never said by the prospect.",
            "difficulty": 1,
        },
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio(loop_scope='session')
async def test_voice_cast_rejects_non_admin_then_lists_eight_for_temp_admin(rep_user):
    c, user_id = rep_user
    forbidden = c.get(api_url("/voice/cast"))
    assert forbidden.status_code == 403, forbidden.text

    async def _set_admin(flag: bool):
        await db.users.update_one({"id": user_id}, {"$set": {"is_admin": flag}})

    await _set_admin(True)
    try:
        r = c.get(api_url("/voice/cast"))
        assert r.status_code == 200, r.text
        cast = r.json()
        assert len(cast) == 8, cast
        for entry in cast:
            assert "character" in entry and "voice_label" in entry, entry
    finally:
        await _set_admin(False)
