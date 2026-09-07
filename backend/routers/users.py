from fastapi import APIRouter, Depends, HTTPException

from lib.analytics import build_dashboard
from lib.auth import current_user, require_self
from lib.db import db
from models.schemas import Dashboard, UserCreate, UserProfile

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    return UserProfile(**me)


@router.patch("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str, payload: UserCreate, me: dict = Depends(current_user)
):
    require_self(user_id, me)
    # Explicit allow-list: xp, level, badges, role escalation and org membership
    # stay server-controlled and can never be set from the browser.
    updates = {
        "name": payload.name.strip()[:80] or me["name"],
        "experience_level": payload.experience_level[:40],
    }
    await db.users.update_one({"id": user_id}, {"$set": updates})
    return UserProfile(**{**me, **updates})


@router.get("/users/{user_id}/dashboard", response_model=Dashboard)
async def dashboard(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sims = (
        await db.simulations.find(
            {"user_id": user_id, "status": "completed"}, {"_id": 0, 'frozen_transcript': 0, 'baseline_evaluation': 0}
        )
        .sort("started_at", 1)
        .to_list(None)
    )
    data = build_dashboard(user, sims)
    data["assignments"] = (
        await db.assignments.find({"user_id": user_id, 'status': 'pending'}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(None)
    )
    if set(data["user"]["badges"]) != set(user.get("badges") or []):
        await db.users.update_one(
            {"id": user_id}, {"$set": {"badges": data["user"]["badges"]}}
        )
    return Dashboard(**data)
