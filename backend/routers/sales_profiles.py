"""Practice My Business: saved sales profiles + AI-generated custom scenarios."""
import secrets

from fastapi import APIRouter, Depends, HTTPException

from lib.catalog import difficulty_by_level, exercise_by_id
from lib.auth import current_user, rate_limit, require_owned, require_self
from lib.db import db
from lib.llm import LlmUnavailable, generate_scenario
from models.schemas import (
    CustomScenario,
    CustomScenarioRequest,
    SalesProfile,
    SalesProfileInput,
)

router = APIRouter(tags=["sales-profiles"])

# Controlled randomisation so repeated practice never yields the same prospect.
VARIATIONS = {
    "personality": [
        "warm and talkative",
        "blunt and impatient",
        "analytical and precise",
        "guarded and defensive",
        "friendly but non-committal",
        "sceptical and testing",
        "distracted and multitasking",
    ],
    "interest": [
        "initially uninterested",
        "mildly curious",
        "actively looking but cautious",
        "interested but overwhelmed",
        "openly dismissive at first",
    ],
    "urgency": [
        "no urgency at all",
        "a soft deadline this quarter",
        "hard deadline within 60 days",
        "urgent but no budget yet",
        "urgency driven by a boss or board",
    ],
    "authority": [
        "sole decision maker",
        "needs one other approver",
        "part of a committee of three",
        "an influencer with no budget",
        "has authority but avoids using it alone",
    ],
    "incumbent": [
        "uses a direct competitor and is locked in for months",
        "uses spreadsheets and manual process",
        "recently left a provider after a bad experience",
        "evaluating two other vendors right now",
        "built something internally that half works",
    ],
    "style": [
        "short clipped answers",
        "long tangential stories",
        "asks more questions than they answer",
        "interrupts frequently",
        "pauses a lot and thinks out loud",
    ],
}


def _variation() -> dict[str, str]:
    return {k: secrets.choice(v) for k, v in VARIATIONS.items()}


PUBLIC_SCENARIO_KEYS = (
    "id",
    "user_id",
    "profile_id",
    "exercise_id",
    "difficulty",
    "product",
    "seller_role",
    "prospect_name",
    "prospect_role",
    "company",
    "company_size",
    "industry",
    "known",
    "objective",
    "mood",
    "personality",
    "objections",
    "created_at",
)


@router.post("/users/{user_id}/sales-profiles", response_model=SalesProfile)
async def create_profile(
    user_id: str, payload: SalesProfileInput, me: dict = Depends(current_user)
):
    require_self(user_id, me)
    if not payload.company.strip() or not payload.product.strip():
        raise HTTPException(status_code=422, detail="Company and product are required")
    profile = SalesProfile(user_id=user_id, **payload.model_dump())
    await db.sales_profiles.insert_one(profile.model_dump())
    return profile


@router.get("/users/{user_id}/sales-profiles", response_model=list[SalesProfile])
async def list_profiles(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    docs = (
        await db.sales_profiles.find({"user_id": user_id}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(50)
    )
    return [SalesProfile(**d) for d in docs]


@router.get("/sales-profiles/{profile_id}", response_model=SalesProfile)
async def get_profile(profile_id: str, me: dict = Depends(current_user)):
    doc = await db.sales_profiles.find_one({"id": profile_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Sales profile not found")
    require_owned(doc, me, "Sales profile")
    return SalesProfile(**doc)


@router.patch("/sales-profiles/{profile_id}", response_model=SalesProfile)
async def update_profile(
    profile_id: str, payload: SalesProfileInput, me: dict = Depends(current_user)
):
    doc = await db.sales_profiles.find_one({"id": profile_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Sales profile not found")
    require_owned(doc, me, "Sales profile")
    updates = payload.model_dump()
    await db.sales_profiles.update_one({"id": profile_id}, {"$set": updates})
    return SalesProfile(**{**doc, **updates})


@router.delete("/sales-profiles/{profile_id}")
async def delete_profile(profile_id: str, me: dict = Depends(current_user)):
    doc = await db.sales_profiles.find_one({"id": profile_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Sales profile not found")
    require_owned(doc, me, "Sales profile")
    res = await db.sales_profiles.delete_one({"id": profile_id})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Sales profile not found")
    return {"deleted": True}


@router.post("/custom-scenarios", response_model=CustomScenario)
async def create_custom_scenario(
    payload: CustomScenarioRequest, me: dict = Depends(current_user)
):
    rate_limit(
        f"scenario:{me['id']}", 30, 3600, "Too many scenario builds. Please try again later."
    )
    profile = await db.sales_profiles.find_one({"id": payload.profile_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Sales profile not found")
    require_owned(profile, me, "Sales profile")
    exercise = exercise_by_id(payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    difficulty = difficulty_by_level(payload.difficulty)
    if not difficulty:
        raise HTTPException(status_code=422, detail="Difficulty must be 1-5")

    try:
        generated = await generate_scenario(
            profile, exercise, difficulty, _variation(), payload.preferences
        )
    except LlmUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Scenario generation failed: {exc}"
        ) from exc

    doc = {
        "user_id": profile["user_id"],
        "profile_id": profile["id"],
        "exercise_id": exercise["id"],
        "difficulty": difficulty["level"],
        "product": profile.get("product") or "your product",
        "seller_role": f"Salesperson at {profile.get('company')}",
        "hidden": generated.get("hidden", ""),
        **{k: generated[k] for k in generated if k != "hidden"},
    }
    scenario = CustomScenario(**{k: v for k, v in doc.items() if k != "hidden"})
    stored = {**scenario.model_dump(), "hidden": doc["hidden"], "profile": profile}
    await db.custom_scenarios.insert_one(stored)
    return scenario
