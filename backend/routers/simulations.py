import logging
import secrets
import asyncio
import uuid
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pydantic import ValidationError

from lib.analytics import summarize
from lib.auth import current_user, rate_limit, require_owned, require_self
from lib.catalog import (
    difficulty_by_level,
    exercise_by_id,
    level_for_xp,
    scenario_by_id,
    scenarios_for_exercise,
)
from lib.curriculum import focus_categories, graded_principles
from lib.dates import today_iso
from lib.journeys import journey_by_id, scenario_for_stage
from lib.db import db
from lib.lifecycle import guarded_start
from lib.security import lease
from lib.voicecast import snapshot
from lib.grading import rubric_for, validate_grade, RUBRIC_VERSION
from lib.llm import _credential
from lib.evidence import record_event
from lib.llm import (
    EvalRequest,
    LlmUnavailable,
    moment_reprise,
    coaching_hint,
    evaluate_conversation,
    prospect_opening,
    prospect_turn,
)
from models.schemas import (
    Evaluation,
    MomentRetryRequest,
    Hint,
    Simulation,
    SimulationStart,
    SimulationSummary,
    TranscriptTurn,
    TurnRequest,
    TurnResponse,
)

router = APIRouter(tags=["simulations"])
logger = logging.getLogger(__name__)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


PERSONA_RULES = [
    (("impatient", "rushed", "quick", "interruption"), "impatient_founder"),
    (("cfo", "financial", "analytical", "procurement"), "analytical_cfo"),
    (("owner", "friendly", "warm", "talkative"), "friendly_owner"),
    (("sceptical", "skeptical", "defensive", "testing"), "skeptical_director"),
    (("guarded", "operations", "cautious"), "guarded_operations"),
    (("vp", "executive", "director", "chief"), "rushed_executive"),
]


def voice_persona_for(scenario: dict) -> str:
    """Map the generated persona to an ElevenLabs voice so tone matches behaviour."""
    blob = " ".join(
        str(scenario.get(k, "")).lower()
        for k in ("personality", "mood", "prospect_role")
    )
    for keywords, persona in PERSONA_RULES:
        if any(k in blob for k in keywords):
            return persona
    return "default"


def _shield(sim: dict) -> dict:
    """Hidden scenario intel is withheld while the call is live and revealed
    afterwards so the coaching can show what could have been discovered."""
    scenario = dict(sim.get("scenario") or {})
    scenario.pop("exercise_ids", None)
    if sim.get("status") != "completed":
        scenario.pop("hidden", None)
        scenario.pop("personality", None)
    public = {**sim, 'scenario': scenario}
    # No internal grading locks or frozen copies in the response model.
    return public


async def _load(sim_id: str, me: dict) -> dict:
    """Load a simulation the caller owns. A foreign id looks identical to a
    missing one, so simulation ids cannot be enumerated."""
    sim = await db.simulations.find_one({"id": sim_id}, {"_id": 0})
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    require_owned(sim, me, "Simulation")
    return sim


async def _guard_new_simulation(me: dict) -> None:
    """Cost + concurrency guard before any paid work is started."""
    await rate_limit(
        f"start:{me['id']}", 40, 3600, "Too many simulations started. Please wait a few minutes."
    )
    active = await db.simulations.count_documents({"user_id": me["id"], "status": "active"})
    if active >= 3:
        raise HTTPException(
            status_code=409,
            detail="You already have live simulations open. End one before starting another.",
        )


async def _resolve_scenario(payload: SimulationStart, exercise: dict, me: dict) -> dict:
    """Pick the scenario for this run: a journey stage, the rep's own custom
    scenario, an explicitly requested one, or a random one for the exercise."""
    if payload.journey_id:
        journey = journey_by_id(payload.journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Unknown journey")
        scenario = scenario_for_stage(journey, payload.exercise_id)
        if not scenario:
            raise HTTPException(
                status_code=422,
                detail=f"{journey['character']} has no {exercise['name']} stage in this journey",
            )
        return scenario
    if payload.custom_scenario_id:
        custom = await db.custom_scenarios.find_one(
            {"id": payload.custom_scenario_id}, {"_id": 0}
        )
        if not custom:
            raise HTTPException(status_code=404, detail="Custom scenario not found")
        require_owned(custom, me, "Custom scenario")
        return _scenario_from_custom(custom)
    scenario = (
        scenario_by_id(payload.scenario_id)
        if payload.scenario_id
        else secrets.choice(scenarios_for_exercise(payload.exercise_id))
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return scenario


@router.post("/simulations", response_model=Simulation)
@guarded_start
async def start_simulation(payload: SimulationStart, me: dict = Depends(current_user)):
    # Identity comes from the session cookie; a user_id in the body is ignored.
    payload.user_id = me["id"]
    exercise = exercise_by_id(payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    difficulty = difficulty_by_level(payload.difficulty)
    if not difficulty:
        raise HTTPException(status_code=422, detail="Difficulty must be 1-5")
    scenario = await _resolve_scenario(payload, exercise, me)

    sim = Simulation(
        user_id=payload.user_id,
        exercise_id=exercise["id"],
        exercise_name=exercise["name"],
        difficulty=difficulty["level"],
        difficulty_name=difficulty["name"],
        scenario=scenario,
        mode=payload.mode,
        voice_persona=voice_persona_for(scenario),
        voice_config=snapshot(scenario, voice_persona_for(scenario)),
        assignment_id=payload.assignment_id,
        is_demo=payload.is_demo,
        rubric_version=RUBRIC_VERSION,
        rubric_snapshot=rubric_for(payload.exercise_id),
    )
    if payload.assignment_id:
        assignment = await db.assignments.find_one({'id': payload.assignment_id, 'user_id': me['id'],
            'workspace_id': me['workspace_id'], 'exercise_id': sim.exercise_id,
            'difficulty': sim.difficulty, 'status': 'pending', 'membership_unverified': {'$ne': True}})
        if not assignment:
            raise HTTPException(422, 'This assignment does not match the exercise, difficulty or workspace')
    prior = await journey_memory(payload.user_id, scenario.get("journey_id"))
    sim.journey_id = scenario.get("journey_id")
    sim.prior_context = prior
    try:
        opening = await prospect_opening(sim.id, scenario, exercise, difficulty, prior)
        sim.transcript = [TranscriptTurn(speaker="prospect", text=opening, at=0.0)]
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("prospect opening failed")
        raise HTTPException(
            status_code=502, detail="AI prospect could not be reached. Please try again."
        ) from exc

    await db.simulations.insert_one(sim.model_dump())
    if sim.is_demo:
        await record_event('demo_started', sim.model_dump())
    return Simulation(**_shield(sim.model_dump()))


async def _guard_turn(sim: dict, me: dict) -> None:
    """Live-call guards: the session must be active, bounded in length, and the
    rep must not be able to hammer paid turns."""
    await rate_limit(f"turn:{me['id']}", 50 if me.get('is_guest') else 240, 3600, "Too many turns. Please slow down.")
    if sim["status"] != "active":
        raise HTTPException(status_code=409, detail="Simulation already completed")
    if len(sim.get("transcript") or []) >= 120:
        raise HTTPException(
            status_code=409,
            detail="This call has reached its maximum length — end it to get your scorecard.",
        )


async def _prospect_reply(sim: dict, transcript: list[dict], text: str) -> str:
    """Generate the buyer's answer, rolling the rep's line back on failure so a
    client retry cannot duplicate it."""
    sim_id = sim["id"]
    try:
        return await prospect_turn(
            sim_id,
            sim["scenario"],
            exercise_by_id(sim["exercise_id"]),
            difficulty_by_level(sim["difficulty"]),
            transcript,
            text,
            sim.get("prior_context") or "",
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail='The AI prospect is unavailable. Your speech is saved.') from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("prospect turn failed")
        raise HTTPException(
            status_code=502, detail="The AI prospect could not be reached."
        ) from exc


@router.post("/simulations/{sim_id}/turns", response_model=TurnResponse)
async def add_turn(
    sim_id: str, payload: TurnRequest, me: dict = Depends(current_user)
):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Empty utterance")
    async with lease(f'turn:{sim_id}', 110):
        sim = await _load(sim_id, me)
        transcript = sim.get('transcript') or []
        existing = next((t for t in transcript if t.get('request_key') == payload.idempotency_key and t['speaker'] == 'rep'), None)
        answer = next((t for t in transcript if t.get('request_key') == payload.idempotency_key and t['speaker'] == 'prospect'), None)
        if existing and existing['text'] != text:
            raise HTTPException(409, 'Idempotency key belongs to different speech')
        if answer:
            return TurnResponse(reply=answer['text'], turn_index=transcript.index(answer), version=sim.get('version', 0), transcript=transcript)
        await _guard_turn(sim, me)
        if not existing:
            version = sim.get('version', 0)
            if payload.expected_version is not None and payload.expected_version != version:
                raise HTTPException(409, 'Conversation changed. Reload the saved transcript before sending.')
            rep = TranscriptTurn(speaker='rep', text=text, at=payload.at, request_key=payload.idempotency_key).model_dump()
            saved = await db.simulations.find_one_and_update({'id': sim_id, 'status': 'active',
                '$or': [{'version': version}, {'version': {'$exists': False}}]},
                {'$push': {'transcript': rep}, '$inc': {'version': 1}}, return_document=ReturnDocument.AFTER)
            if not saved:
                raise HTTPException(409, 'Call ended before this speech was accepted')
            transcript = saved['transcript'][:-1]
        else:
            transcript = transcript[:transcript.index(existing)]
        try:
            reply = await asyncio.wait_for(_prospect_reply(sim, transcript, text), timeout=90)
        except Exception:
            await db.simulations.update_one({'id': sim_id, 'status': 'active'}, {'$set': {'failed_turn_key': payload.idempotency_key}})
            raise HTTPException(502, 'Your speech is saved. Retry this reply or end the call for coaching.') from None
        turn = TranscriptTurn(speaker='prospect', text=reply, at=payload.at, request_key=payload.idempotency_key).model_dump()
        stored = await db.simulations.find_one_and_update({'id': sim_id, 'status': 'active'},
            {'$push': {'transcript': turn}, '$inc': {'version': 1}, '$unset': {'failed_turn_key': ''}}, return_document=ReturnDocument.AFTER)
        if not stored:
            raise HTTPException(409, 'This call has ended. Your accepted speech is in the frozen transcript.')
        await record_event('first_reply', stored)
        return TurnResponse(reply=reply, turn_index=len(stored['transcript']) - 1, version=stored['version'], transcript=stored['transcript'])


async def _claim_for_grading(sim_id: str) -> dict:
    """Idempotency guard: two rapid End clicks must not produce two analyses or
    double XP. The first request flips the row to "analyzing"; the second bounces."""
    now = datetime.now(timezone.utc)
    claim = await db.simulations.find_one_and_update({'id': sim_id, 'status': 'active', 'transcript.speaker': 'rep'},
        [{'$set': {'status': 'ending', 'frozen_transcript': '$transcript', 'frozen_version': {'$ifNull': ['$version', 0]}, 'ended_at': now}}],
        return_document=ReturnDocument.AFTER)
    if claim:
        return claim
    claim = await db.simulations.find_one({'id': sim_id, 'status': {'$in': ['ending', 'grading_failed']}})
    if not claim:
        raise HTTPException(409, 'This call is already being graded or has no saved speech.')
    return claim


async def _grade(sim: dict, transcript: list[dict], duration: int) -> Evaluation:
    """Run the coaching analysis, releasing the grading claim if it fails so the
    rep can retry ending the call."""
    sim_id = sim["id"]
    try:
        req = EvalRequest(
                simulation_id=sim_id,
                scenario=sim["scenario"],
                exercise=exercise_by_id(sim["exercise_id"]),
                difficulty=difficulty_by_level(sim["difficulty"]),
                transcript=transcript,
                duration_seconds=duration,
                focus=focus_categories(sim["exercise_id"]),
                principles=graded_principles(sim["exercise_id"]),
                prior=sim.get("prior_context") or "",
                rubric=sim.get('rubric_snapshot') or rubric_for(sim['exercise_id'], sim.get('moment_category', '')),
            )
        rubric = sim.get('rubric_snapshot') or rubric_for(sim['exercise_id'], sim.get('moment_category', ''))
        version = sim.get('frozen_version') if sim.get('frozen_version') is not None else sim.get('version', 0)
        return await asyncio.wait_for(_validated_evaluation(req, rubric, version), timeout=90)
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail='Coaching is unavailable. Your frozen conversation is saved.') from exc
    except Exception as exc:  # noqa: BLE001
        # Diagnostic classification only: never model output, quotes, keys or upstream bodies.
        logger.warning('evaluation failed simulation=%s class=%s', sim_id, type(exc).__name__)
        raise HTTPException(
            status_code=502, detail="Coaching analysis failed validation or timed out. Retry grading; the frozen call is preserved."
        ) from exc


async def _validated_evaluation(req: EvalRequest, rubric: dict, version: int) -> Evaluation:
    """At most ONE schema/evidence repair, under the same frozen-call deadline and budget.

    This never retries a committed mutation, never relaxes validation and never
    retries transport/provider failures. A second invalid answer is recoverable failure.
    """
    for attempt in range(2):
        raw = {}
        try:
            raw = await evaluate_conversation(req)
            return Evaluation(**validate_grade(raw, req.transcript, rubric, _credential()[2], version))
        except (ValidationError, ValueError) as exc:
            if attempt:
                raise
            if isinstance(exc, ValidationError):
                codes = [{'field': list(e['loc']), 'rule': e['type']} for e in exc.errors(include_input=False)]
            else:
                codes = ['Recheck exact category labels, evidence quotations and transcript indices; follow the JSON schema.']
            req.repair = {'validation_rules': codes, 'previous_candidate': raw}
    raise ValueError('No validated result')


async def _moment_outcome(sim: dict, evaluation: Evaluation) -> dict:
    """Only a targeted, same-rubric baseline is comparable; ties are not improvement."""
    if sim.get("mode") != "moment":
        return {}
    target = next((c.score for c in evaluation.category_scores if c.category == sim.get('moment_category')), None)
    baseline = sim.get('moment_baseline')
    comparable = baseline is not None and target is not None and sim.get('baseline_model') == evaluation.model_version
    return {'moment_score': target, 'moment_improved': target > baseline if comparable else None}


@router.post("/simulations/{sim_id}/complete", response_model=Simulation)
async def complete_simulation(sim_id: str, me: dict = Depends(current_user)):
    sim = await _load(sim_id, me)
    if sim["status"] == "completed":
        await _commit_rewards(sim)
        return Simulation(**_shield(sim))
    transcript = sim.get("transcript") or []
    rep_turns = [t for t in transcript if t["speaker"] == "rep"]
    if not rep_turns:
        raise HTTPException(
            status_code=422,
            detail="No salesperson speech was captured — say something to the prospect before ending the call.",
        )

    # A dead worker's lease expires. Frozen transcript never reopens for speech.
    await db.simulations.update_one({'id': sim_id, 'status': {'$in': ['grading', 'analyzing']},
        'grading_deadline': {'$lt': datetime.now(timezone.utc)}}, {'$set': {'status': 'grading_failed'}})
    async with lease(f'grade:{sim_id}', 110):
        sim = await _claim_for_grading(sim_id)
        transcript = sim['frozen_transcript']
        ended = _aware(sim['ended_at'])
        duration = max(0, int((ended - _aware(sim.get('call_started_at') or sim['started_at'])).total_seconds()))
        token = str(uuid.uuid4())
        await db.simulations.update_one({'id': sim_id}, {'$set': {'status': 'grading', 'grading_token': token,
            'duration_seconds': duration, 'grading_deadline': datetime.now(timezone.utc) + timedelta(seconds=100)}})
        try:
            await rate_limit(f'grading:{me["id"]}', 8 if me.get('is_guest') else 60, 3600, 'Grading allowance reached. Your frozen transcript is saved for later.')
            evaluation = await _grade(sim, transcript, duration)
        except Exception:
            await db.simulations.update_one({'id': sim_id, 'grading_token': token}, {'$set': {'status': 'grading_failed', 'grading_error': 'Analysis could not be validated. Retry grading.'}})
            raise
        xp = round(evaluation.overall_score / 2) + sim['difficulty'] * 10
        updates = {'status': 'completed', 'evaluation': evaluation.model_dump(), 'xp_awarded': xp,
            'rewards_pending': True, 'grading_error': '', 'duration_seconds': duration,
            **await _moment_outcome(sim, evaluation)}
        await db.simulations.update_one({'id': sim_id, 'grading_token': token}, {'$set': updates})
        result = {**sim, **updates}
        await _commit_rewards(result)
        return Simulation(**_shield(result))


async def _close_assignment(sim: dict, score: int, ended: datetime) -> None:
    """A completed call satisfies the oldest matching pending assignment."""
    if not sim.get('assignment_id') or sim.get('mode') == 'moment':
        return
    await db.assignments.update_one(
        {
            'id': sim['assignment_id'],
            "user_id": sim["user_id"],
            "exercise_id": sim["exercise_id"],
            'difficulty': sim['difficulty'],
            'membership_unverified': {'$ne': True},
            "status": "pending",
        },
        {
            "$set": {
                "status": "completed",
                "completed_at": ended,
                "completed_simulation_id": sim["id"],
                "score": score,
            }
        },
    )


async def _commit_rewards(sim: dict):
    if not sim.get('rewards_pending'):
        return
    today = today_iso()
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    # Award marker and counters share ONE atomic user-document update.
    await db.users.update_one({'id': sim['user_id'], 'award_ids': {'$ne': sim['id']}}, [{'$set': {
        'award_ids': {'$concatArrays': [{'$ifNull': ['$award_ids', []]}, [sim['id']]]},
        'xp': {'$add': [{'$ifNull': ['$xp', 0]}, sim['xp_awarded']]},
        'moments_corrected': {'$add': [{'$ifNull': ['$moments_corrected', 0]}, 1 if sim.get('moment_improved') else 0]},
        'streak': {'$cond': [{'$eq': ['$last_practice_date', today]}, '$streak', {'$cond': [{'$eq': ['$last_practice_date', yesterday]}, {'$add': [{'$ifNull': ['$streak', 0]}, 1]}, 1]}]},
        'last_practice_date': today,
    }}, {'$set': {'level': {'$add': [1, {'$floor': {'$sqrt': {'$divide': ['$xp', 250]}}}]}}}])
    await _close_assignment(sim, sim['evaluation']['overall_score'], sim['ended_at'])
    await record_event('grading_completed', sim)
    if sim.get('retry_of'):
        await record_event('retry_completed', sim)
    if sim.get('moment_improved') is True:
        await record_event('comparable_improvement', sim)
    await db.simulations.update_one({'id': sim['id']}, {'$set': {'rewards_pending': False}})


@router.post('/simulations/{sim_id}/activate', response_model=Simulation)
async def activate(sim_id: str, me: dict = Depends(current_user)):
    sim = await _load(sim_id, me)
    if sim['status'] == 'preparation':
        await db.simulations.update_one({'id': sim_id, 'status': 'preparation'}, {'$set': {
            'status': 'active', 'call_started_at': datetime.now(timezone.utc)}})
        sim = await _load(sim_id, me)
    if sim['status'] != 'active':
        raise HTTPException(409, 'This call is no longer active')
    await record_event('practice_started', sim)
    return Simulation(**_shield(sim))


@router.post('/simulations/{sim_id}/abandon', response_model=Simulation)
async def abandon(sim_id: str, me: dict = Depends(current_user)):
    await _load(sim_id, me)
    await db.simulations.update_one({'id': sim_id, 'status': {'$in': ['preparation', 'active']}},
        {'$set': {'status': 'abandoned', 'ended_at': datetime.now(timezone.utc)}})
    return Simulation(**_shield(await _load(sim_id, me)))


async def _award(user_id: str, xp: int) -> None:
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return
    today = today_iso()
    last = user.get("last_practice_date")
    streak = user.get("streak", 0)
    if last == today:
        pass
    elif last == (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat():
        streak += 1
    else:
        streak = 1
    total_xp = user.get("xp", 0) + xp
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "xp": total_xp,
                "level": level_for_xp(total_xp),
                "streak": streak,
                "last_practice_date": today,
            }
        },
    )


@router.post("/simulations/{sim_id}/retry", response_model=Simulation)
@guarded_start
async def retry_simulation(sim_id: str, me: dict = Depends(current_user)):
    """Re-run the exact same prospect and difficulty, so attempts are comparable."""
    old = await _load(sim_id, me)
    if old['status'] != 'completed' or old.get('mode') == 'moment':
        raise HTTPException(409, 'Full retries require a completed full call')
    exercise = exercise_by_id(old["exercise_id"])
    difficulty = difficulty_by_level(old["difficulty"])
    if not exercise or not difficulty:
        raise HTTPException(status_code=422, detail="This simulation cannot be retried")

    sim = Simulation(
        user_id=old["user_id"],
        exercise_id=old["exercise_id"],
        exercise_name=old["exercise_name"],
        difficulty=old["difficulty"],
        difficulty_name=old["difficulty_name"],
        scenario=old["scenario"],
        mode=old.get("mode", "guided"),
        voice_persona=old.get("voice_persona") or voice_persona_for(old["scenario"]),
        voice_config=old.get('voice_config') or snapshot(old['scenario'], old.get('voice_persona', 'default')),
        retry_of=old['id'],
        is_demo=old.get('is_demo', False),
        prior_context=old.get('prior_context', ''),
        rubric_version=old.get('rubric_version', 'consultative-v1'),
        rubric_snapshot=old.get('rubric_snapshot') or rubric_for(old['exercise_id']),
        assisted=True,
    )
    try:
        opening = await prospect_opening(sim.id, old["scenario"], exercise, difficulty, sim.prior_context)
        sim.transcript = [TranscriptTurn(speaker="prospect", text=opening, at=0.0)]
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("retry opening failed")
        raise HTTPException(
            status_code=502, detail="AI prospect could not be reached. Please try again."
        ) from exc

    await db.simulations.insert_one(sim.model_dump())
    await record_event('retry_started', sim.model_dump())
    return Simulation(**_shield(sim.model_dump()))


def _pick_moment(old: dict, miss_index: int) -> tuple[dict, dict]:
    """Validate that this call has a graded coaching moment at that index."""
    evaluation = old.get("evaluation") or {}
    misses = evaluation.get("misses") or []
    if old["status"] != "completed" or not misses:
        raise HTTPException(
            status_code=409, detail="This call has no graded coaching moments to retry."
        )
    if miss_index >= len(misses):
        raise HTTPException(status_code=404, detail="Coaching moment not found")
    return evaluation, misses[miss_index]


async def _build_reprise(sim_id: str, old: dict, miss: dict) -> dict:
    """Ask the coach model to rebuild the situation and the buyer's re-opening line."""
    exercise = exercise_by_id(old["exercise_id"])
    difficulty = difficulty_by_level(old["difficulty"])
    if not exercise or not difficulty:
        raise HTTPException(status_code=422, detail="This moment cannot be retried")
    try:
        return await moment_reprise(
            sim_id, old["scenario"], exercise, difficulty, old.get("transcript") or [], miss
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("moment reprise failed")
        raise HTTPException(
            status_code=502, detail="The coaching moment could not be rebuilt."
        ) from exc


def _moment_simulation(
    user_id: str, old: dict, miss: dict, evaluation: dict, setup: dict
) -> Simulation:
    return Simulation(
        user_id=user_id,
        exercise_id=old["exercise_id"],
        exercise_name=old["exercise_name"],
        difficulty=old["difficulty"],
        difficulty_name=old["difficulty_name"],
        scenario=old["scenario"],
        mode="moment",
        is_demo=old.get('is_demo', False),
        assisted=True,
        voice_config=old.get('voice_config') or snapshot(old['scenario'], old.get('voice_persona', 'default')),
        voice_persona=old.get("voice_persona") or voice_persona_for(old["scenario"]),
        journey_id=old.get("journey_id"),
        retry_of=old["id"],
        moment_label=str(miss.get("title") or "Coaching moment"),
        moment_situation=setup["situation"],
        moment_objective=setup["objective"],
        origin_score=int(evaluation.get("overall_score") or 0),
        # The buyer re-opens the moment; from there the conversation is live again.
        transcript=[TranscriptTurn(speaker="prospect", text=setup["buyer_line"], at=0.0)],
        prior_context=(
            "You are mid-conversation with this salesperson. "
            f"Context: {setup['situation']}"
        ),
    )


@router.post("/simulations/{sim_id}/retry-moment", response_model=Simulation)
@guarded_start
async def retry_moment(
    sim_id: str, payload: MomentRetryRequest, me: dict = Depends(current_user)
):
    """Retry That Moment: re-enter one coaching moment from a graded call instead
    of replaying the whole simulation. The original attempt and its score are
    never modified — this is practice after the assessment."""
    old = await _load(sim_id, me)
    evaluation, miss = _pick_moment(old, payload.miss_index)
    turns = old.get('frozen_transcript') or old['transcript']
    index = miss.get('turn_index')
    # Legacy quotes may be anchored only when exactly one saved turn matches.
    if index is None:
        matches = [i for i, t in enumerate(turns) if miss.get('quote') and miss['quote'] in t['text']]
        if len(matches) != 1:
            raise HTTPException(409, 'This older coaching note has no exact evidence anchor. Retry the full call instead.')
        index = matches[0]
    if index >= len(turns) or miss.get('quote', '') not in turns[index]['text']:
        raise HTTPException(409, 'This coaching moment has no valid transcript anchor')
    buyer_index = max((i for i in range(index + 1) if turns[i]['speaker'] == 'prospect'), default=0)
    category = miss.get('category') or next((c['category'] for c in evaluation.get('category_scores', []) if c['category'] in rubric_for(old['exercise_id'])['weights']), '')
    if not category:
        raise HTTPException(409, 'No assessable target skill for this moment')
    setup = {'situation': 'Replay the exchange immediately before this missed opportunity.',
             'objective': f"Practise {category}: {miss.get('better_approach') or miss['title']}",
             'buyer_line': turns[buyer_index]['text']}
    sim = _moment_simulation(me["id"], old, miss, evaluation, setup)
    sim.moment_category = category
    sim.source_turn_index = index
    sim.rubric_snapshot = rubric_for(old['exercise_id'], category)
    sim.rubric_version = RUBRIC_VERSION
    sim.scenario = {**old['scenario'], 'objective': setup['objective']}
    sim.prior_context = json.dumps(turns[:buyer_index], default=str) + '\nCURRENT MOMENT OBJECTIVE: ' + setup['objective']
    baseline_turns = turns[buyer_index:min(len(turns), max(index + 2, buyer_index + 2))]
    baseline = await _grade(sim.model_dump(), baseline_turns, 0)
    sim.moment_baseline = next((c.score for c in baseline.category_scores if c.category == category), None)
    await db.simulations.insert_one({**sim.model_dump(), 'baseline_model': baseline.model_version, 'baseline_evaluation': baseline.model_dump()})
    await record_event('retry_started', sim.model_dump())
    return Simulation(**_shield(sim.model_dump()))


@router.get("/simulations/{sim_id}", response_model=Simulation)
async def get_simulation(sim_id: str, me: dict = Depends(current_user)):
    return Simulation(**_shield(await _load(sim_id, me)))


@router.get("/users/{user_id}/simulations", response_model=list[SimulationSummary])
async def list_simulations(user_id: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=200), me: dict = Depends(current_user)):
    require_self(user_id, me)
    sims = (
        await db.simulations.find({"user_id": user_id}, {"_id": 0})
        .sort("started_at", -1)
        .skip(offset).to_list(limit)
    )
    return [SimulationSummary(**summarize(s)) for s in sims]


def _lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").split("\n") if line.strip()]


def _product_sheet(profile: dict, custom: dict) -> dict:
    """The rep's own product facts, in the shape the prospect engine reads."""
    return {
        "name": profile.get("product") or custom.get("product") or "your product",
        "one_liner": profile.get("product_description") or "",
        "features": _lines(profile.get("benefits")),
        "benefits": _lines(profile.get("problems_solved")),
        "pricing": profile.get("pricing") or "",
        "differentiators": _lines(profile.get("differentiators")),
        "limitations": [],
        "use_cases": [profile.get("ideal_customer")] if profile.get("ideal_customer") else [],
    }


def _scenario_from_custom(custom: dict) -> dict:
    """Turn a stored AI-generated scenario into the scenario shape the prospect
    engine and brief screens expect, carrying the rep's own product sheet."""
    profile = custom.get("profile") or {}
    sheet = _product_sheet(profile, custom)
    return {
        "id": custom["id"],
        "product": custom.get("product") or profile.get("product") or "your product",
        "seller_role": custom.get("seller_role") or f"Salesperson at {profile.get('company', '')}",
        "product_sheet": sheet,
        "things_to_remember": [
            f"Your typical goal on this call: {profile.get('call_goal')}" if profile.get("call_goal") else "",
            f"Competitors in play: {profile.get('competitors')}" if profile.get("competitors") else "",
            f"Methodology: {profile.get('methodology')}" if profile.get("methodology") else "",
        ],
        "prospect_name": custom.get("prospect_name", ""),
        "prospect_role": custom.get("prospect_role", ""),
        "company": custom.get("company", ""),
        "company_size": custom.get("company_size", ""),
        "industry": custom.get("industry", ""),
        "known": custom.get("known", ""),
        "hidden": custom.get("hidden", ""),
        "objective": custom.get("objective", ""),
        "personality": custom.get("personality", ""),
        "mood": custom.get("mood", ""),
        "objections": custom.get("objections", []),
    }


async def journey_memory(user_id: str, journey_id: str | None) -> str:
    """Digest of what this character actually said to this rep in earlier stages."""
    if not journey_id:
        return ""
    sims = (
        await db.simulations.find(
            {"user_id": user_id, "journey_id": journey_id, "status": "completed", 'mode': 'journey', 'retry_of': None},
            {"_id": 0},
        )
        .sort("started_at", 1)
        .to_list(6)
    )
    if not sims:
        return ""
    chunks: list[str] = []
    for s in sims:
        lines = [
            f"  {'Salesperson' if t['speaker'] == 'rep' else 'You'}: {t['text']}"
            for t in (s.get("transcript") or [])[:14]
        ]
        chunks.append(f"- {s['exercise_name']} ({s['difficulty_name']}):\n" + "\n".join(lines))
    return "\n".join(chunks)


@router.get("/simulations/{sim_id}/hint", response_model=Hint)
async def get_hint(sim_id: str, me: dict = Depends(current_user)):
    """Live coaching rail — only offered on the two teaching difficulties."""
    await rate_limit(f"hint:{me['id']}", 20 if me.get('is_guest') else 120, 3600, "Too many coaching hints. Please slow down.")
    sim = await _load(sim_id, me)
    if sim['status'] != 'active':
        raise HTTPException(409, 'Live coaching is only available during an active call')
    if sim["difficulty"] > 2:
        raise HTTPException(
            status_code=409,
            detail="Live hints are only available on Beginner and Developing levels.",
        )
    await db.simulations.update_one({'id': sim_id}, {'$set': {'assisted': True}})
    # Explicit flow: `data` is None until the coach answers, and a None result is
    # turned into an error response rather than being consumed.
    data: dict | None = None
    try:
        data = await coaching_hint(
            sim_id,
            sim["scenario"],
            exercise_by_id(sim["exercise_id"]),
            difficulty_by_level(sim["difficulty"]),
            sim.get("transcript") or [],
            graded_principles(sim["exercise_id"]),
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("hint failed for simulation %s", sim_id)
        raise HTTPException(status_code=502, detail="The coach is unavailable.") from exc
    if not data:
        raise HTTPException(status_code=502, detail="The coach had nothing useful to add.")
    # Level 1 shows the wording outright; Level 2 keeps it behind a reveal.
    return Hint(**data, reveal_example=sim["difficulty"] == 1)
