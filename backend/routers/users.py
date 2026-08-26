from fastapi import APIRouter, HTTPException

from lib.analytics import build_dashboard
from lib.db import db
from models.schemas import Dashboard, UserCreate, UserProfile

router = APIRouter(tags=["users"])


@router.post("/users", response_model=UserProfile)
async def create_user(payload: UserCreate):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    user = UserProfile(
        name=name,
        experience_level=payload.experience_level,
        role=payload.role,
        org=payload.org,
    )
    await db.users.insert_one(user.model_dump())
    return user


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str):
    doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**doc)


@router.patch("/users/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, payload: UserCreate):
    doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    updates = {
        "name": payload.name.strip() or doc["name"],
        "experience_level": payload.experience_level,
        "role": payload.role,
        "org": payload.org,
    }
    await db.users.update_one({"id": user_id}, {"$set": updates})
    return UserProfile(**{**doc, **updates})


@router.get("/users/{user_id}/dashboard", response_model=Dashboard)
async def dashboard(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sims = (
        await db.simulations.find(
            {"user_id": user_id, "status": "completed"}, {"_id": 0}
        )
        .sort("started_at", 1)
        .to_list(500)
    )
    data = build_dashboard(user, sims)
    if set(data["user"]["badges"]) != set(user.get("badges") or []):
        await db.users.update_one(
            {"id": user_id}, {"$set": {"badges": data["user"]["badges"]}}
        )
    return Dashboard(**data)
