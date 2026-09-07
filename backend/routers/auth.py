"""Email + password authentication, plus a guest session for first-time visitors."""
import re
from pymongo.errors import DuplicateKeyError

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from lib.auth import (
    clear_session,
    current_user,
    hash_password,
    issue_session,
    rate_limit,
    verify_password,
    personal_workspace,
)
from lib.security import client_address
from lib.db import db
from models.schemas import LoginRequest, SessionResponse, SignupRequest, UserProfile

router = APIRouter(tags=["auth"], prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def _norm(email: str) -> str:
    return email.strip().lower()


def _client_key(request: Request, suffix: str) -> str:
    """All preview/production traffic arrives through a proxy, so the socket peer
    is shared by every visitor. Prefer the forwarded client address."""
    host = client_address(request)
    return f"{suffix}:{host}"


def _profile(doc: dict) -> UserProfile:
    return UserProfile(**{k: v for k, v in doc.items() if k != "password"})


@router.post("/signup", response_model=SessionResponse)
async def signup(payload: SignupRequest, request: Request, response: Response):
    await rate_limit(
        _client_key(request, "signup"), 60, 3600, "Too many sign-up attempts. Try again later."
    )
    email = _norm(payload.email)
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    if await db.users.find_one({"email": email}):
        # Neutral message: does not confirm whether the address exists.
        raise HTTPException(
            status_code=409, detail="That email cannot be used. Try signing in instead."
        )
    user = UserProfile(name=name, experience_level=payload.experience_level, org=payload.org)
    doc = user.model_dump()
    doc["email"] = email
    doc["password"] = hash_password(payload.password)
    doc["is_guest"] = False
    try:
        await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, 'That email cannot be used. Try signing in instead.') from None
    doc = await personal_workspace(doc)
    return SessionResponse(user=_profile(doc), token=await issue_session(response, user.id))


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, request: Request, response: Response):
    await rate_limit(
        _client_key(request, "login"), 30, 300, "Too many attempts. Try again in a few minutes."
    )
    email = _norm(payload.email)
    doc = await db.users.find_one({"email": email}, {"_id": 0})
    if not doc or not verify_password(payload.password, doc.get("password", "")):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    doc = await personal_workspace(doc)
    return SessionResponse(user=_profile(doc), token=await issue_session(response, doc["id"]))


@router.post("/guest", response_model=SessionResponse)
async def guest(request: Request, response: Response):
    """Demo path: a throwaway account so judges reach the core loop with no signup."""
    await rate_limit(
        _client_key(request, "guest"), 30, 3600, "Too many guest sessions from this network."
    )
    user = UserProfile(name="Guest Rep", experience_level="New")
    doc = user.model_dump()
    doc["is_guest"] = True
    await db.users.insert_one(doc)
    doc = await personal_workspace(doc)
    return SessionResponse(user=_profile(doc), token=await issue_session(response, user.id))


@router.get("/me", response_model=UserProfile)
async def me(user: dict = Depends(current_user)):
    return _profile(user)


@router.post("/logout")
async def logout(response: Response, me: dict = Depends(current_user)):
    await db.users.update_one({'id': me['id']}, {'$inc': {'auth_epoch': 1}})
    clear_session(response)
    return {"ok": True}
