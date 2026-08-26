"""Criterion: Mic check buyer-audio test uses the assigned ElevenLabs voice.

Mic check's "Test buyer audio" button issues POST /api/voice/speak with the
character name and difficulty exactly as MicCheck.tsx does. Verify it returns
200 audio/mpeg (not a browser-voice fallback) for an authenticated user.
"""

import pytest

from .conftest import api_url, signup_user

TIMEOUT = 60.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-mic-check-voice", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def test_voice_speak_with_character_returns_audio(rep_user):
    c, _ = rep_user
    res = c.post(
        api_url("/voice/speak"),
        json={"text": "Hey, this is Jordan.", "character": "Jordan Miller", "difficulty": 1},
    )
    assert res.status_code == 200, res.text
    assert res.headers.get("content-type", "").startswith("audio/"), res.headers
    assert len(res.content) > 1000, "expected non-trivial audio payload"
