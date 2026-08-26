"""ElevenLabs voice proxy. The API key never leaves the server: the browser posts
text here and receives audio bytes back.

There is no generic-TTS fallback in the simulation path — if the approved voice
for a character cannot be produced, the caller gets an error and shows a visible
retry rather than silently degrading to a robotic browser voice."""
import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from lib.auth import current_user, rate_limit
from lib.voicecast import cast_entries, resolve
from models.schemas import VoiceStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech"
VOICES_URL = "https://api.elevenlabs.io/v1/voices"
# multilingual_v2 is noticeably more human than the turbo models: better prosody,
# breaths and emotional range. Worth the extra few hundred ms for realism.
MODEL_ID = "eleven_multilingual_v2"

# Difficulty nudges delivery within the character's own range: a harder buyer is
# terser and less warm, but it is still recognisably the same person.
DIFFICULTY_TRIM = {1: 0.04, 2: 0.02, 3: 0.0, 4: -0.03, 5: -0.06}


def _humanise(text: str) -> str:
    """Light punctuation shaping so the model breathes like a person on a phone call."""
    out = text.replace(" - ", " — ").replace("...", "…")
    for filler in ("Look,", "Honestly,", "I mean,", "Well,", "Right,", "Hmm,", "Okay,"):
        out = out.replace(f"{filler} ", f"{filler}… ")
    return out


def _key() -> str | None:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    return key or None


class SpeakRequest(BaseModel):
    # Bounded so one request cannot burn an arbitrary amount of paid credit. The
    # client names a character/persona — never a raw voice id.
    text: str = Field(max_length=1200)
    character: str = Field(default="", max_length=80)
    persona: str = Field(default="default", max_length=60)
    difficulty: int = Field(default=2, ge=1, le=5)


class CastVoice(BaseModel):
    character: str
    role: str
    voice_label: str
    style_note: str
    stability: float
    similarity_boost: float
    speed: float
    verified: bool
    detail: str = ""


@router.get("/voice/status", response_model=VoiceStatus)
async def voice_status():
    if _key():
        return VoiceStatus(
            provider="elevenlabs",
            available=True,
            message="ElevenLabs voices active.",
            voices=[f"{c['character']} — {c['voice_label']}" for c in cast_entries()],
        )
    return VoiceStatus(
        provider="browser",
        available=False,
        message=(
            "ElevenLabs is wired up but no credential is configured. Add "
            "ELEVENLABS_API_KEY to backend/.env — simulations will not start "
            "with a generic robotic voice."
        ),
        voices=[],
    )


@router.get("/voice/cast", response_model=list[CastVoice])
async def voice_cast(me: dict = Depends(current_user)):
    """Voice Cast QA: the fixed cast plus live verification of each voice id."""
    key = _key()
    out: list[CastVoice] = []
    async with httpx.AsyncClient(timeout=20) as client:
        for entry in cast_entries():
            verified, detail = False, "No ElevenLabs credential configured"
            if key:
                try:
                    res = await client.get(
                        f"{VOICES_URL}/{entry['voice_id']}", headers={"xi-api-key": key}
                    )
                    verified = res.status_code == 200
                    detail = (
                        (res.json().get("name") or entry["voice_label"])
                        if verified
                        else f"ElevenLabs returned {res.status_code}"
                    )
                except httpx.HTTPError:
                    detail = "ElevenLabs unreachable"
            out.append(
                CastVoice(
                    character=entry["character"],
                    role=entry["role"],
                    voice_label=entry["voice_label"],
                    style_note=entry["style_note"],
                    stability=entry["settings"]["stability"],
                    similarity_boost=entry["settings"]["similarity_boost"],
                    speed=entry["settings"]["speed"],
                    verified=verified,
                    detail=detail,
                )
            )
    return out


def _delivery(voice: dict, difficulty: int) -> dict:
    """The character's own settings, nudged (not replaced) by difficulty."""
    settings = dict(voice["settings"])
    settings["stability"] = round(
        min(0.75, max(0.2, settings["stability"] + DIFFICULTY_TRIM.get(difficulty, 0.0))), 2
    )
    return {**settings, "use_speaker_boost": True}


async def _synthesize(voice: dict, text: str, settings: dict) -> bytes:
    """One ElevenLabs call. Upstream errors are logged, never forwarded, because
    their bodies can echo account/credential detail."""
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                f"{ELEVEN_URL}/{voice['voice_id']}",
                headers={"xi-api-key": _key(), "Content-Type": "application/json"},
                json={"text": _humanise(text), "model_id": MODEL_ID, "voice_settings": settings},
            )
    except httpx.HTTPError as exc:
        logger.warning("elevenlabs unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="The prospect voice is unavailable.") from exc
    if res.status_code >= 400:
        logger.warning("elevenlabs tts failed with %s", res.status_code)
        raise HTTPException(status_code=502, detail="The prospect voice is unavailable.")
    return res.content


@router.post("/voice/speak")
async def speak(payload: SpeakRequest, me: dict = Depends(current_user)):
    # Paid resource: authenticated callers only, with a per-user hourly ceiling.
    rate_limit(
        f"tts:{me['id']}", 400, 3600, "Voice limit reached for now. Please try again later."
    )
    key = _key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="ELEVENLABS_API_KEY is not configured in backend/.env.",
        )
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="No text to speak")

    voice = resolve(payload.character, payload.persona)
    settings = _delivery(voice, payload.difficulty)
    logger.info(
        "tts character=%s voice=%s model=%s difficulty=%s",
        voice["character"],
        voice["voice_label"],
        MODEL_ID,
        payload.difficulty,
    )
    audio = await _synthesize(voice, text, settings)
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"X-Voice-Character": voice["character"], "X-Voice-Label": voice["voice_label"]},
    )
