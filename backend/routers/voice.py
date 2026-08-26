"""ElevenLabs voice proxy. The API key never leaves the server: the browser posts
text here and receives audio bytes back. Falls back to browser speech synthesis
client-side when no key is configured."""
import os

import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from models.schemas import VoiceStatus

router = APIRouter(tags=["voice"])

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech"
# multilingual_v2 is noticeably more human than the turbo models: better prosody,
# breaths and emotional range. Worth the extra few hundred ms for realism.
MODEL_ID = "eleven_multilingual_v2"

# Persona → ElevenLabs stock voice. Matched to the prospect archetypes the
# simulator generates so voice and behaviour reinforce each other.
VOICES: dict[str, dict[str, str]] = {
    "rushed_executive": {"id": "pNInz6obpgDQGcFmaJgB", "label": "Adam — brisk executive"},
    "analytical_cfo": {"id": "VR6AewLTigWG4xSOukaG", "label": "Arnold — measured, analytical"},
    "friendly_owner": {"id": "ErXwobaYiN019PkySvjV", "label": "Antoni — warm, conversational"},
    "skeptical_director": {"id": "EXAVITQu4vr4xnSDxMaL", "label": "Bella — composed, sceptical"},
    "guarded_operations": {"id": "21m00Tcm4TlvDq8ikWAM", "label": "Rachel — even, guarded"},
    "impatient_founder": {"id": "MF3mGyEYCl7XYWbV9V6O", "label": "Elli — quick, impatient"},
    "default": {"id": "21m00Tcm4TlvDq8ikWAM", "label": "Rachel — neutral"},
}

# Difficulty and mood shape delivery: higher difficulty is terser and less warm.
STYLE_BY_DIFFICULTY = {
    1: {"stability": 0.42, "similarity_boost": 0.85, "style": 0.35},
    2: {"stability": 0.38, "similarity_boost": 0.85, "style": 0.42},
    3: {"stability": 0.34, "similarity_boost": 0.88, "style": 0.5},
    4: {"stability": 0.3, "similarity_boost": 0.9, "style": 0.58},
    5: {"stability": 0.26, "similarity_boost": 0.92, "style": 0.68},
}


def _humanise(text: str) -> str:
    """Light punctuation shaping so the model breathes like a person on a phone call."""
    out = text.replace(" - ", " — ").replace("...", "…")
    for filler in ("Look,", "Honestly,", "I mean,", "Well,", "Right,"):
        out = out.replace(f"{filler} ", f"{filler}… ")
    return out


def _key() -> str | None:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    return key or None


class SpeakRequest(BaseModel):
    text: str
    persona: str = "default"
    difficulty: int = 2


@router.get("/voice/status", response_model=VoiceStatus)
async def voice_status():
    if _key():
        return VoiceStatus(
            provider="elevenlabs",
            available=True,
            message="ElevenLabs voices active.",
            voices=[v["label"] for v in VOICES.values()],
        )
    return VoiceStatus(
        provider="browser",
        available=False,
        message=(
            "ElevenLabs is wired up but no credential is configured. Add "
            "ELEVENLABS_API_KEY to backend/.env to switch the prospect to a "
            "natural ElevenLabs voice; until then the browser's built-in speech "
            "synthesis is used."
        ),
        voices=[],
    )


@router.post("/voice/speak")
async def speak(payload: SpeakRequest):
    key = _key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="ELEVENLABS_API_KEY is not configured in backend/.env.",
        )
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="No text to speak")

    voice = VOICES.get(payload.persona, VOICES["default"])
    settings = STYLE_BY_DIFFICULTY.get(payload.difficulty, STYLE_BY_DIFFICULTY[2])
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                f"{ELEVEN_URL}/{voice['id']}",
                headers={"xi-api-key": key, "Content-Type": "application/json"},
                json={
                    "text": _humanise(text),
                    "model_id": MODEL_ID,
                    "voice_settings": {**settings, "use_speaker_boost": True},
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"ElevenLabs unreachable: {exc}") from exc

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs returned {res.status_code}: {res.text[:200]}",
        )
    return Response(content=res.content, media_type="audio/mpeg")
