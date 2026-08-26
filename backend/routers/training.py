from fastapi import APIRouter, Depends, HTTPException

from lib.catalog import (
    DIFFICULTIES,
    EXERCISES,
    STAGES,
    SKILL_CATEGORIES,
    exercise_by_id,
    scenarios_for_exercise,
)
from lib.auth import current_user, require_self
from lib.db import db
from lib.journeys import JOURNEYS, journey_by_id, public_journey
from models.schemas import Difficulty, Exercise, JourneyView, ScenarioBrief

router = APIRouter(tags=["training"])

PUBLIC_KEYS = (
    "id",
    "product",
    "seller_role",
    "product_sheet",
    "things_to_remember",
    "prospect_name",
    "prospect_role",
    "company",
    "company_size",
    "industry",
    "known",
    "objective",
    "mood",
    "objections",
)


def public_scenario(s: dict) -> dict:
    return {k: s[k] for k in PUBLIC_KEYS if k in s}


@router.get("/exercises", response_model=list[Exercise])
async def list_exercises():
    return EXERCISES


@router.get("/difficulties", response_model=list[Difficulty])
async def list_difficulties():
    return DIFFICULTIES


@router.get("/skills", response_model=list[str])
async def list_skills():
    return SKILL_CATEGORIES


@router.get("/exercises/{exercise_id}/scenarios", response_model=list[ScenarioBrief])
async def list_scenarios(exercise_id: str):
    if not exercise_by_id(exercise_id):
        raise HTTPException(status_code=404, detail="Unknown exercise")
    return [public_scenario(s) for s in scenarios_for_exercise(exercise_id)]


@router.get("/stages")
async def list_stages():
    """The recommended learning order. Nothing is hard-locked — this is guidance."""
    return STAGES


@router.get("/users/{user_id}/journeys", response_model=list[JourneyView])
async def list_journeys(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    sims = await db.simulations.find(
        {"user_id": user_id, "status": "completed"}, {"_id": 0}
    ).to_list(500)
    out = []
    for j in JOURNEYS:
        view = public_journey(j)
        done = 0
        for stage in view["stages"]:
            matches = [
                s
                for s in sims
                if s.get("journey_id") == j["id"] and s["exercise_id"] == stage["exercise_id"]
            ]
            if matches:
                best = max(matches, key=lambda s: (s.get("evaluation") or {}).get("overall_score", 0))
                stage["completed"] = True
                stage["best_score"] = (best.get("evaluation") or {}).get("overall_score")
                stage["simulation_id"] = best["id"]
                done += 1
        view["completed_stages"] = done
        nxt = next((st for st in view["stages"] if not st["completed"]), None)
        view["next_exercise_id"] = nxt["exercise_id"] if nxt else None
        out.append(view)
    return out


@router.get("/journeys/{journey_id}", response_model=JourneyView)
async def get_journey(journey_id: str):
    j = journey_by_id(journey_id)
    if not j:
        raise HTTPException(status_code=404, detail="Unknown journey")
    return public_journey(j)
