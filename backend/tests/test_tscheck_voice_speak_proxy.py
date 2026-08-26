"""Criterion: no regression in the ElevenLabs proxy after speak() was split
into _delivery + _synthesize.

- POST /api/voice/speak with {text, character:'Jordan Miller', difficulty:3}
  -> 200 audio/mpeg with X-Voice-Character/X-Voice-Label headers.
- Anonymous caller -> 401.
- Text over the 1200-char cap -> 422.
- An unknown character name still succeeds (falls back to the persona
  archetype voice).
- /api/voice/cast still lists 8 verified voices.
"""

import httpx
import pytest

from .conftest import API_URL, api_url, signup_user

TIMEOUT = 60.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-voice-speak-proxy", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def test_speak_with_known_character_returns_audio_with_headers(rep_user):
    c, _ = rep_user
    r = c.post(
        api_url("/voice/speak"),
        json={"text": "Hey, this is Jordan.", "character": "Jordan Miller", "difficulty": 3},
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("audio/mpeg"), r.headers
    assert r.headers.get("x-voice-character"), r.headers
    assert r.headers.get("x-voice-label"), r.headers


def test_speak_anonymous_returns_401():
    with httpx.Client(base_url=API_URL, timeout=TIMEOUT) as c:
        r = c.post(
            "/voice/speak",
            json={"text": "Hello there", "character": "Jordan Miller", "difficulty": 3},
        )
        assert r.status_code == 401, r.text


def test_speak_text_over_cap_returns_422(rep_user):
    c, _ = rep_user
    r = c.post(
        api_url("/voice/speak"),
        json={"text": "x" * 1201, "character": "Jordan Miller", "difficulty": 3},
    )
    assert r.status_code == 422, r.text


def test_speak_unknown_character_falls_back_and_succeeds(rep_user):
    c, _ = rep_user
    r = c.post(
        api_url("/voice/speak"),
        json={
            "text": "This character name does not exist.",
            "character": "Not A Real Character Name",
            "persona": "default",
            "difficulty": 3,
        },
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("audio/mpeg"), r.headers
    assert r.headers.get("x-voice-character"), r.headers


def test_voice_cast_lists_eight_verified_voices(rep_user):
    c, _ = rep_user
    r = c.get(api_url("/voice/cast"))
    assert r.status_code == 200, r.text
    cast = r.json()
    assert len(cast) == 8, cast
    for entry in cast:
        assert entry["verified"] is True, entry
