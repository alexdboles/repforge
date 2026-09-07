"""Authentication and abuse-control primitives.

Identity is carried by a signed JWT in an httpOnly cookie — never by a user_id
sent from the browser. Every user-owned route derives the caller from the cookie
and verifies ownership server-side.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, Header, HTTPException, Response

from lib.db import db
from lib.security import rate_limit

COOKIE_NAME = "repforge_session"
ALGORITHM = "HS256"
SESSION_DAYS = 14
# The bearer token handed to the browser is deliberately much shorter-lived than
# the httpOnly cookie: it is the fallback for cookie-blocked contexts (preview
# iframes) and is the only piece of the session that JS can read.
BEARER_HOURS = 12


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        # Fail closed: without a signing secret we cannot issue trustworthy sessions.
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    return secret


def hash_password(password: str) -> str:
    if len(password.encode('utf-8')) > 72:
        raise HTTPException(422, 'Password must be at most 72 UTF-8 bytes; accented characters may use more than one byte.')
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


async def issue_session(response: Response, user_id: str) -> str:
    """Set the session cookie and also hand the token back to the caller.

    The cookie is the primary mechanism (httpOnly, Secure, SameSite=None so it
    still works when the app is embedded in a preview iframe). Browsers that
    block third-party cookies drop it anyway, so the same token is returned in
    the body and replayed as an Authorization header — otherwise sign-in loops
    back to the login screen inside an iframe.
    """
    now = datetime.now(timezone.utc)
    user = await db.users.find_one({'id': user_id})
    epoch = (user or {}).get('auth_epoch', 0)
    sid = str(uuid.uuid4())
    cookie_token = jwt.encode(
        {"sub": user_id, "epoch": epoch, "sid": sid, "exp": now + timedelta(days=SESSION_DAYS)},
        _secret(),
        algorithm=ALGORITHM,
    )
    bearer_token = jwt.encode(
        {"sub": user_id, "epoch": epoch, "sid": sid, "exp": now + timedelta(hours=BEARER_HOURS)},
        _secret(),
        algorithm=ALGORITHM,
    )
    response.set_cookie(
        COOKIE_NAME,
        cookie_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return bearer_token


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


async def session_actor(repforge_session=None, authorization=None):
    bearer = authorization.split(' ', 1)[1].strip() if isinstance(authorization, str) and authorization.lower().startswith('bearer ') else ''
    for token in (repforge_session, bearer):
        if not isinstance(token, str) or not token:
            continue
        try:
            claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            continue
        user = await db.users.find_one({'id': claims.get('sub')}, {'_id': 0, 'password': 0})
        if user and claims.get('epoch', 0) == user.get('auth_epoch', 0):
            return user
    return None


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
    for token in (repforge_session, bearer):
        if not isinstance(token, str) or not token:
            continue
        try:
            claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            continue
        user = await db.users.find_one({'id': claims.get('sub')}, {'_id': 0, 'password': 0})
        if user and claims.get('epoch', 0) == user.get('auth_epoch', 0):
            if user.get('privacy_lock'):
                raise HTTPException(409, 'Your data is being deleted. Please wait.')
            if not user.get('workspace_id'):
                user = await personal_workspace(user)
            membership = await db.memberships.find_one({'workspace_id': user['workspace_id'], 'user_id': user['id'], 'verified': True})
            if not membership:
                raise HTTPException(403, 'Workspace membership needs verification')
            user['workspace_role'] = membership['role']
            return user
    raise HTTPException(401, 'Sign in to continue')


def require_self(user_id: str, user: dict) -> None:
    """Ownership gate for /users/{user_id}/... style routes."""
    if user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not your resource")


def require_owned(doc: dict, user: dict, label: str = "Resource") -> None:
    """Ownership gate for a fetched document. 404 rather than 403 so ids stay unenumerable."""
    if doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail=f"{label} not found")


async def personal_workspace(user: dict) -> dict:
    wid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"repforge:personal:{user['id']}"))
    await db.workspaces.update_one({'id': wid}, {'$setOnInsert': {
        'id': wid, 'name': user.get('org') or 'Personal', 'kind': 'personal', 'owner_id': user['id']}}, upsert=True)
    await db.memberships.update_one({'workspace_id': wid, 'user_id': user['id']}, {'$setOnInsert': {
        'workspace_id': wid, 'user_id': user['id'], 'role': 'owner', 'verified': True}}, upsert=True)
    if not user.get('workspace_id'):
        user['workspace_id'] = wid
        await db.users.update_one({'id': user['id']}, {'$set': {'workspace_id': wid, 'personal_workspace_id': wid}})
    membership = await db.memberships.find_one({'workspace_id': user['workspace_id'], 'user_id': user['id'], 'verified': True})
    user['workspace_role'] = membership['role'] if membership else 'member'
    return user


def require_org(org: str, user: dict) -> None:
    """Tenant boundary: team data is visible only inside the caller's own org."""
    if not org or org != user.get('workspace_id'):
        raise HTTPException(403, 'Not your workspace')


def require_manager(user: dict):
    if user.get('workspace_role') not in ('owner', 'admin', 'manager') or user.get('is_guest'):
        raise HTTPException(403, 'Manager permission required')


def require_admin(user: dict):
    if not user.get('is_admin'):
        raise HTTPException(403, 'Administrator permission required')
