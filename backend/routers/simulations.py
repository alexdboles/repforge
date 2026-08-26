import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

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
    return {**sim, "scenario": scenario}


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
    rate_limit(
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
async def start_simulation(payload: SimulationStart, me: dict = Depends(current_user)):
    # Identity comes from the session cookie; a user_id in the body is ignored.
    payload.user_id = me["id"]
    await _guard_new_simulation(me)
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
    )
    prior = await journey_memory(payload.user_id, scenario.get("journey_id"))
    sim.journey_id = scenario.get("journey_id")
    sim.prior_context = prior
    try:
        opening = await prospect_opening(sim.id, scenario, exercise, difficulty, prior)
        sim.transcript = [TranscriptTurn(speaker="prospect", text=opening, at=0.0)]
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("prospect opening failed")
        raise HTTPException(
            status_code=502, detail=f"AI prospect could not be reached: {exc}"
        ) from exc

    await db.simulations.insert_one(sim.model_dump())
    return Simulation(**_shield(sim.model_dump()))


def _guard_turn(sim: dict, me: dict) -> None:
    """Live-call guards: the session must be active, bounded in length, and the
    rep must not be able to hammer paid turns."""
    rate_limit(f"turn:{me['id']}", 240, 3600, "Too many turns. Please slow down.")
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
        await db.simulations.update_one({"id": sim_id}, {"$pop": {"transcript": 1}})
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        await db.simulations.update_one({"id": sim_id}, {"$pop": {"transcript": 1}})
        logger.exception("prospect turn failed")
        raise HTTPException(
            status_code=502, detail="The AI prospect could not be reached."
        ) from exc


@router.post("/simulations/{sim_id}/turns", response_model=TurnResponse)
async def add_turn(
    sim_id: str, payload: TurnRequest, me: dict = Depends(current_user)
):
    text = payload.text.strip()[:2000]
    if not text:
        raise HTTPException(status_code=422, detail="Empty utterance")
    sim = await _load(sim_id, me)
    _guard_turn(sim, me)

    transcript = sim.get("transcript") or []
    # Persist what the rep said BEFORE the LLM call. Ending the call mid-generation
    # must still grade the words they actually spoke, and the prospect's late reply
    # must never be able to arrive without them.
    await db.simulations.update_one(
        {"id": sim_id},
        {"$push": {"transcript": {"speaker": "rep", "text": text, "at": payload.at}}},
    )
    reply = await _prospect_reply(sim, transcript, text)

    # The call may have been ended while the prospect was "thinking": the reply is
    # then dropped entirely — it never reaches the transcript or the scoring.
    stored = await db.simulations.update_one(
        {"id": sim_id, "status": "active"},
        {"$push": {"transcript": {"speaker": "prospect", "text": reply, "at": payload.at}}},
    )
    if stored.modified_count != 1:
        raise HTTPException(status_code=409, detail="This call has already ended.")
    return TurnResponse(reply=reply, turn_index=len(transcript) + 1)


async def _claim_for_grading(sim_id: str) -> None:
    """Idempotency guard: two rapid End clicks must not produce two analyses or
    double XP. The first request flips the row to "analyzing"; the second bounces."""
    claim = await db.simulations.update_one(
        {"id": sim_id, "status": "active"}, {"$set": {"status": "analyzing"}}
    )
    if claim.modified_count != 1:
        raise HTTPException(status_code=409, detail="This call is already being graded.")


async def _grade(sim: dict, transcript: list[dict], duration: int) -> Evaluation:
    """Run the coaching analysis, releasing the grading claim if it fails so the
    rep can retry ending the call."""
    sim_id = sim["id"]
    try:
        raw = await evaluate_conversation(
            EvalRequest(
                simulation_id=sim_id,
                scenario=sim["scenario"],
                exercise=exercise_by_id(sim["exercise_id"]),
                difficulty=difficulty_by_level(sim["difficulty"]),
                transcript=transcript,
                duration_seconds=duration,
                focus=focus_categories(sim["exercise_id"]),
                principles=graded_principles(sim["exercise_id"]),
                prior=sim.get("prior_context") or "",
            )
        )
        return Evaluation(**raw)
    except LlmUnavailable as exc:
        await db.simulations.update_one({"id": sim_id}, {"$set": {"status": "active"}})
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("evaluation failed for simulation %s", sim_id)
        await db.simulations.update_one({"id": sim_id}, {"$set": {"status": "active"}})
        raise HTTPException(
            status_code=502, detail="Coaching analysis failed. Please try ending the call again."
        ) from exc


async def _moment_outcome(sim: dict, score: int) -> dict:
    """Retry That Moment result: did this attempt beat the original call?"""
    if sim.get("mode") != "moment":
        return {}
    improved = score >= int(sim.get("origin_score") or 0)
    if improved:
        await db.users.update_one({"id": sim["user_id"]}, {"$inc": {"moments_corrected": 1}})
    return {"moment_improved": improved}


@router.post("/simulations/{sim_id}/complete", response_model=Simulation)
async def complete_simulation(sim_id: str, me: dict = Depends(current_user)):
    sim = await _load(sim_id, me)
    if sim["status"] == "completed":
        return Simulation(**_shield(sim))
    transcript = sim.get("transcript") or []
    rep_turns = [t for t in transcript if t["speaker"] == "rep"]
    if not rep_turns:
        raise HTTPException(
            status_code=422,
            detail="No salesperson speech was captured — say something to the prospect before ending the call.",
        )

    await _claim_for_grading(sim_id)

    ended = datetime.now(timezone.utc)
    duration = max(1, int((ended - _aware(sim["started_at"])).total_seconds()))
    evaluation = await _grade(sim, transcript, duration)

    xp = round(evaluation.overall_score / 2) + sim["difficulty"] * 10
    updates = {
        "status": "completed",
        "ended_at": ended,
        "duration_seconds": duration,
        "evaluation": evaluation.model_dump(),
        "xp_awarded": xp,
        **await _moment_outcome(sim, evaluation.overall_score),
    }
    await db.simulations.update_one({"id": sim_id}, {"$set": updates})
    await _award(sim["user_id"], xp)
    await _close_assignment(sim, evaluation.overall_score, ended)
    return Simulation(**_shield({**sim, **updates}))


async def _close_assignment(sim: dict, score: int, ended: datetime) -> None:
    """A completed call satisfies the oldest matching pending assignment."""
    await db.assignments.update_one(
        {
            "user_id": sim["user_id"],
            "exercise_id": sim["exercise_id"],
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
async def retry_simulation(sim_id: str, me: dict = Depends(current_user)):
    """Re-run the exact same prospect and difficulty, so attempts are comparable."""
    rate_limit(f"start:{me['id']}", 40, 3600, "Too many simulations started. Please wait a few minutes.")
    old = await _load(sim_id, me)
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
    )
    try:
        opening = await prospect_opening(sim.id, old["scenario"], exercise, difficulty)
        sim.transcript = [TranscriptTurn(speaker="prospect", text=opening, at=0.0)]
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("retry opening failed")
        raise HTTPException(
            status_code=502, detail=f"AI prospect could not be reached: {exc}"
        ) from exc

    await db.simulations.insert_one(sim.model_dump())
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
async def retry_moment(
    sim_id: str, payload: MomentRetryRequest, me: dict = Depends(current_user)
):
    """Retry That Moment: re-enter one coaching moment from a graded call instead
    of replaying the whole simulation. The original attempt and its score are
    never modified — this is practice after the assessment."""
    rate_limit(f"start:{me['id']}", 40, 3600, "Too many retries started. Please wait a few minutes.")
    old = await _load(sim_id, me)
    evaluation, miss = _pick_moment(old, payload.miss_index)
    setup = await _build_reprise(sim_id, old, miss)
    sim = _moment_simulation(me["id"], old, miss, evaluation, setup)
    await db.simulations.insert_one(sim.model_dump())
    return Simulation(**_shield(sim.model_dump()))


@router.get("/simulations/{sim_id}", response_model=Simulation)
async def get_simulation(sim_id: str, me: dict = Depends(current_user)):
    return Simulation(**_shield(await _load(sim_id, me)))


@router.get("/users/{user_id}/simulations", response_model=list[SimulationSummary])
async def list_simulations(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    sims = (
        await db.simulations.find({"user_id": user_id}, {"_id": 0})
        .sort("started_at", -1)
        .to_list(200)
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
            {"user_id": user_id, "journey_id": journey_id, "status": "completed"},
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
    rate_limit(f"hint:{me['id']}", 120, 3600, "Too many coaching hints. Please slow down.")
    sim = await _load(sim_id, me)
    if sim["difficulty"] > 2:
        raise HTTPException(
            status_code=409,
            detail="Live hints are only available on Beginner and Developing levels.",
        )
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
