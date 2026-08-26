import logging
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from lib.analytics import summarize
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
    LlmUnavailable,
    coaching_hint,
    evaluate_conversation,
    prospect_opening,
    prospect_turn,
)
from models.schemas import (
    Evaluation,
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


async def _load(sim_id: str) -> dict:
    sim = await db.simulations.find_one({"id": sim_id}, {"_id": 0})
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@router.post("/simulations", response_model=Simulation)
async def start_simulation(payload: SimulationStart):
    exercise = exercise_by_id(payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    difficulty = difficulty_by_level(payload.difficulty)
    if not difficulty:
        raise HTTPException(status_code=422, detail="Difficulty must be 1-5")
    user = await db.users.find_one({"id": payload.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    elif payload.custom_scenario_id:
        custom = await db.custom_scenarios.find_one(
            {"id": payload.custom_scenario_id}, {"_id": 0}
        )
        if not custom:
            raise HTTPException(status_code=404, detail="Custom scenario not found")
        scenario = _scenario_from_custom(custom)
    else:
        scenario = (
            scenario_by_id(payload.scenario_id)
            if payload.scenario_id
            else random.choice(scenarios_for_exercise(payload.exercise_id))
        )
    if not scenario:
        raise HTTPException(status_code=404, detail="Unknown scenario")

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


@router.post("/simulations/{sim_id}/turns", response_model=TurnResponse)
async def add_turn(sim_id: str, payload: TurnRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Empty utterance")
    sim = await _load(sim_id)
    if sim["status"] != "active":
        raise HTTPException(status_code=409, detail="Simulation already completed")

    exercise = exercise_by_id(sim["exercise_id"])
    difficulty = difficulty_by_level(sim["difficulty"])
    transcript = sim.get("transcript") or []
    try:
        reply = await prospect_turn(
            sim_id,
            sim["scenario"],
            exercise,
            difficulty,
            transcript,
            text,
            sim.get("prior_context") or "",
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("prospect turn failed")
        raise HTTPException(
            status_code=502, detail=f"AI prospect could not be reached: {exc}"
        ) from exc

    new_turns = [
        {"speaker": "rep", "text": text, "at": payload.at},
        {"speaker": "prospect", "text": reply, "at": payload.at},
    ]
    await db.simulations.update_one(
        {"id": sim_id}, {"$push": {"transcript": {"$each": new_turns}}}
    )
    return TurnResponse(reply=reply, turn_index=len(transcript) + 1)


@router.post("/simulations/{sim_id}/complete", response_model=Simulation)
async def complete_simulation(sim_id: str):
    sim = await _load(sim_id)
    if sim["status"] == "completed":
        return Simulation(**_shield(sim))
    transcript = sim.get("transcript") or []
    rep_turns = [t for t in transcript if t["speaker"] == "rep"]
    if not rep_turns:
        raise HTTPException(
            status_code=422,
            detail="No salesperson speech was captured — say something to the prospect before ending the call.",
        )

    ended = datetime.now(timezone.utc)
    duration = max(1, int((ended - _aware(sim["started_at"])).total_seconds()))
    exercise = exercise_by_id(sim["exercise_id"])
    difficulty = difficulty_by_level(sim["difficulty"])
    try:
        raw = await evaluate_conversation(
            sim_id,
            sim["scenario"],
            exercise,
            difficulty,
            transcript,
            duration,
            focus=focus_categories(sim["exercise_id"]),
            principles=graded_principles(sim["exercise_id"]),
            prior=sim.get("prior_context") or "",
        )
        evaluation = Evaluation(**raw)
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("evaluation failed")
        raise HTTPException(
            status_code=502, detail=f"Coaching analysis failed: {exc}"
        ) from exc

    xp = round(evaluation.overall_score / 2) + sim["difficulty"] * 10
    updates = {
        "status": "completed",
        "ended_at": ended,
        "duration_seconds": duration,
        "evaluation": evaluation.model_dump(),
        "xp_awarded": xp,
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
async def retry_simulation(sim_id: str):
    """Re-run the exact same prospect and difficulty, so attempts are comparable."""
    old = await _load(sim_id)
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


@router.get("/simulations/{sim_id}", response_model=Simulation)
async def get_simulation(sim_id: str):
    return Simulation(**_shield(await _load(sim_id)))


@router.get("/users/{user_id}/simulations", response_model=list[SimulationSummary])
async def list_simulations(user_id: str):
    sims = (
        await db.simulations.find({"user_id": user_id}, {"_id": 0})
        .sort("started_at", -1)
        .to_list(200)
    )
    return [SimulationSummary(**summarize(s)) for s in sims]


def _scenario_from_custom(custom: dict) -> dict:
    """Turn a stored AI-generated scenario into the scenario shape the prospect
    engine and brief screens expect, carrying the rep's own product sheet."""
    profile = custom.get("profile") or {}
    sheet = {
        "name": profile.get("product") or custom.get("product") or "your product",
        "one_liner": profile.get("product_description") or "",
        "features": [f for f in (profile.get("benefits") or "").split("\n") if f.strip()],
        "benefits": [b for b in (profile.get("problems_solved") or "").split("\n") if b.strip()],
        "pricing": profile.get("pricing") or "",
        "differentiators": [
            d for d in (profile.get("differentiators") or "").split("\n") if d.strip()
        ],
        "limitations": [],
        "use_cases": [profile.get("ideal_customer") or ""] if profile.get("ideal_customer") else [],
    }
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
async def get_hint(sim_id: str):
    """Live coaching rail — only offered on the two teaching difficulties."""
    sim = await _load(sim_id)
    if sim["difficulty"] > 2:
        raise HTTPException(
            status_code=409,
            detail="Live hints are only available on Beginner and Developing levels.",
        )
    exercise = exercise_by_id(sim["exercise_id"])
    difficulty = difficulty_by_level(sim["difficulty"])
    try:
        data = await coaching_hint(
            sim_id,
            sim["scenario"],
            exercise,
            difficulty,
            sim.get("transcript") or [],
            graded_principles(sim["exercise_id"]),
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("hint failed")
        raise HTTPException(status_code=502, detail=f"Coach unavailable: {exc}") from exc
    # Level 1 shows the wording outright; Level 2 keeps it behind a reveal.
    return Hint(**data, reveal_example=sim["difficulty"] == 1)
