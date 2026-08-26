from fastapi import APIRouter, HTTPException

from lib.catalog import (
    DIFFICULTIES,
    EXERCISES,
    SKILL_CATEGORIES,
    exercise_by_id,
    scenarios_for_exercise,
)
from models.schemas import Difficulty, Exercise, ScenarioBrief

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
