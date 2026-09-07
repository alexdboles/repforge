"""Criterion: Mic check buyer-audio test uses the assigned ElevenLabs voice.

Mic check's "Test buyer audio" button issues POST /api/voice/sample with the
simulation_id exactly as MicCheck.tsx does (post-hardening contract — the sample
line is derived server-side from the simulation's own voice_config, not an
arbitrary client-supplied character/text). Verify it returns 200 audio/mpeg (not
a browser-voice fallback) for an authenticated user, and 404 for another user's
simulation.
"""

import pytest

from .conftest import api_url, signup_user

TIMEOUT = 60.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-mic-check-voice", timeout=TIMEOUT)
    yield c, user_id
    c.close()


@pytest.fixture
def other_user():
    c, user_id, _ = signup_user("tscheck-mic-check-voice-other", timeout=TIMEOUT)
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
    return r.json()["id"]


def test_voice_sample_for_own_simulation_returns_audio(rep_user):
    c, user_id = rep_user
    sim_id = _start_sim(c, user_id)
    res = c.post(api_url("/voice/sample"), json={"simulation_id": sim_id})
    assert res.status_code == 200, res.text
    assert res.headers.get("content-type", "").startswith("audio/"), res.headers
    assert len(res.content) > 1000, "expected non-trivial audio payload"


def test_voice_sample_for_other_users_simulation_returns_404(rep_user, other_user):
    c, user_id = rep_user
    other_c, _ = other_user
    sim_id = _start_sim(c, user_id)
    res = other_c.post(api_url("/voice/sample"), json={"simulation_id": sim_id})
    assert res.status_code == 404, res.text
