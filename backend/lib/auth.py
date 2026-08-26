"""Authentication and abuse-control primitives.

Identity is carried by a signed JWT in an httpOnly cookie — never by a user_id
sent from the browser. Every user-owned route derives the caller from the cookie
and verifies ownership server-side.
"""
import os
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, Header, HTTPException, Response

from lib.db import db

COOKIE_NAME = "repforge_session"
ALGORITHM = "HS256"
SESSION_DAYS = 14


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        # Fail closed: without a signing secret we cannot issue trustworthy sessions.
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    return secret


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_session(response: Response, user_id: str) -> str:
    """Set the session cookie and also hand the token back to the caller.

    The cookie is the primary mechanism (httpOnly, Secure, SameSite=None so it
    still works when the app is embedded in a preview iframe). Browsers that
    block third-party cookies drop it anyway, so the same token is returned in
    the body and replayed as an Authorization header — otherwise sign-in loops
    back to the login screen inside an iframe.
    """
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    token = jwt.encode(
        {"sub": user_id, "exp": expires}, _secret(), algorithm=ALGORITHM
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return token


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


async def current_user(
    repforge_session: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    """The authenticated caller, or 401. Never trusts a client-supplied user id.

    Accepts the session cookie or an `Authorization: Bearer <token>` header — the
    header path keeps sign-in working where third-party cookies are blocked.
    """
    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
    token = bearer or repforge_session
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    try:
        claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Your session has expired") from None
    user = await db.users.find_one({"id": claims.get("sub")}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Your session has expired")
    return user


def require_self(user_id: str, user: dict) -> None:
    """Ownership gate for /users/{user_id}/... style routes."""
    if user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not your resource")


def require_owned(doc: dict, user: dict, label: str = "Resource") -> None:
    """Ownership gate for a fetched document. 404 rather than 403 so ids stay unenumerable."""
    if doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail=f"{label} not found")


# ---------- abuse control ----------
# In-process fixed-window counters. Enough to stop one client burning paid
# ElevenLabs/LLM calls; a multi-worker deployment would move this to Mongo/Redis.
_BUCKETS: dict[str, list[float]] = {}


def rate_limit(key: str, limit: int, window_seconds: int, message: str) -> None:
    now = time.time()
    hits = [t for t in _BUCKETS.get(key, []) if now - t < window_seconds]
    if len(hits) >= limit:
        _BUCKETS[key] = hits
        raise HTTPException(status_code=429, detail=message)
    hits.append(now)
    _BUCKETS[key] = hits


def require_org(org: str, user: dict) -> None:
    """Tenant boundary: team data is visible only inside the caller's own org."""
    caller_org = (user.get("org") or "").strip()
    if not org or not caller_org or org.strip().lower() != caller_org.lower():
        raise HTTPException(status_code=403, detail="Not your organisation")
