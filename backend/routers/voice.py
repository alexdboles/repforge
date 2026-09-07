"""ElevenLabs voice proxy. The API key never leaves the server: the browser posts
text here and receives audio bytes back.

There is no generic-TTS fallback in the simulation path — if the approved voice
for a character cannot be produced, the caller gets an error and shows a visible
retry rather than silently degrading to a robotic browser voice."""
import logging
import os
import json
import time
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from lib.auth import current_user, rate_limit, require_admin, require_owned
from lib.voicecast import cast_entries, resolve, snapshot
from lib.db import db
from lib.security import digest, provider_budget, lease
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
    text: str = Field(default='', max_length=2000)
    simulation_id: str = Field(min_length=1, max_length=80)
    turn_id: str = Field(default='', max_length=80)
    character: str = Field(default="", max_length=80)
    persona: str = Field(default="default", max_length=60)
    difficulty: int = Field(default=2, ge=1, le=5)


class SampleRequest(BaseModel):
    simulation_id: str = Field(min_length=1, max_length=80)


class QASampleRequest(BaseModel):
    character: str = Field(max_length=80)
    line: int = Field(default=0, ge=0, le=2)


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
            message="Voice configured. Provider reachability and playback are checked separately.",
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
    require_admin(me)
    cached = await db.provider_checks.find_one({'_id': 'voice-cast', 'expires_at': {'$gt': datetime.now(timezone.utc)}})
    if cached:
        return [CastVoice(**x) for x in cached['voices']]
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
    await db.provider_checks.replace_one({'_id': 'voice-cast'}, {'voices': [v.model_dump() for v in out], 'expires_at': datetime.now(timezone.utc) + timedelta(minutes=15)}, upsert=True)
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
    await provider_budget('tts', len(text))
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                f"{ELEVEN_URL}/{voice['voice_id']}",
                headers={"xi-api-key": _key(), "Content-Type": "application/json"},
                json={"text": _humanise(text), "model_id": MODEL_ID, "voice_settings": settings},
            )
    except httpx.HTTPError as exc:
        logger.warning("elevenlabs unreachable")
        raise HTTPException(status_code=502, detail="The prospect voice is unavailable.") from exc
    if res.status_code >= 400:
        logger.warning("elevenlabs tts failed with %s", res.status_code)
        raise HTTPException(status_code=502, detail="The prospect voice is unavailable.")
    logger.info('tts completed latency_ms=%d bytes=%d', int((time.monotonic() - started) * 1000), len(res.content))
    return res.content


@router.post("/voice/speak")
async def speak(payload: SpeakRequest, me: dict = Depends(current_user)):
    # Paid resource: authenticated callers only, with a per-user hourly ceiling.
    await rate_limit(
        f"tts:{me['id']}", 80 if me.get('is_guest') else 400, 3600, "Voice limit reached for now. Please try again later."
    )
    key = _key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="Prospect voice is not configured. Typed practice is available.",
        )
    sim = await _owned_voice_sim(payload.simulation_id, me)
    turn = next((t for t in sim.get('transcript', []) if t['speaker'] == 'prospect' and
        ((payload.turn_id and t.get('id') == payload.turn_id) or (not payload.turn_id and t['text'] == payload.text))), None)
    if not turn:
        raise HTTPException(404, 'Saved prospect turn not found')
    voice = sim.get('voice_config') or snapshot(sim['scenario'], sim.get('voice_persona', 'default'))
    audio = await _cached_audio(me['id'], voice, turn['text'], sim['difficulty'])
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"X-Voice-Character": voice["character"], "X-Voice-Label": voice["voice_label"]},
    )


async def _owned_voice_sim(sim_id, me):
    sim = await db.simulations.find_one({'id': sim_id}, {'_id': 0})
    if not sim:
        raise HTTPException(404, 'Simulation not found')
    require_owned(sim, me)
    if not sim.get('voice_config'):
        sim['voice_config'] = snapshot(sim['scenario'], sim.get('voice_persona', 'default'))
        await db.simulations.update_one({'id': sim_id, 'voice_config': {'$exists': False}}, {'$set': {'voice_config': sim['voice_config']}})
    return sim


async def _cached_audio(owner, voice, text, difficulty):
    settings = _delivery(voice, difficulty)
    cache_id = digest(json.dumps([owner, voice, text, settings, MODEL_ID], sort_keys=True))
    cached = await db.audio_cache.find_one({'_id': cache_id, 'expires_at': {'$gt': datetime.now(timezone.utc)}})
    if cached:
        return cached['audio']
    async with lease(f'audio:{cache_id}', 60):
        audio = await _synthesize(voice, text, settings)
        if len(audio) > 8_000_000:
            raise HTTPException(502, 'Voice response exceeded the safe size limit')
        await db.audio_cache.replace_one({'_id': cache_id}, {'audio': audio,
            'expires_at': datetime.now(timezone.utc) + timedelta(days=1)}, upsert=True)
        return audio


@router.post('/voice/sample')
async def sample(payload: SampleRequest, me: dict = Depends(current_user)):
    await rate_limit(f'sample:{me["id"]}', 12, 3600, 'Audio check allowance reached')
    sim = await _owned_voice_sim(payload.simulation_id, me)
    if not _key():
        raise HTTPException(503, 'Voice unavailable. You can use typed practice.')
    voice = sim['voice_config']
    text = f"Hello, this is {sim['scenario']['prospect_name'].split()[0]}. Can you hear me?"
    return Response(await _cached_audio(me['id'], voice, text, sim['difficulty']), media_type='audio/mpeg')


@router.post('/voice/qa-sample')
async def qa_sample(payload: QASampleRequest, me: dict = Depends(current_user)):
    require_admin(me)
    await rate_limit(f'qa-sample:{me["id"]}', 30, 3600, 'Voice QA allowance reached')
    if payload.character not in {v['character'] for v in cast_entries()}:
        raise HTTPException(422, 'Choose an approved voice')
    lines = ["Okay, I understand what you're saying, but honestly we're pretty happy with what we use today. So what would actually make this worth changing?",
             "Hmm… maybe. I'm just not convinced that's really the problem we're trying to solve.",
             "I've got two minutes. Give me the short version."]
    return Response(await _cached_audio(me['id'], resolve(payload.character), lines[payload.line], 3), media_type='audio/mpeg')
