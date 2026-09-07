"""Emergent-managed Google identity exchange with bounded, fail-closed linking.

Never trust an email, subject, role or verified flag from the frontend. The
documented provider response omits email_verified: absent != verified.
"""
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException, Response
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from lib.auth import issue_session, personal_workspace, verify_password
from lib.db import db
from lib.security import digest, lease
from lib.data_guard import data_operation
from models.google_auth import ManagedGoogleIdentity, GoogleExchangeResponse
from models.schemas import SessionResponse, UserProfile

SESSION_DATA_URL = 'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data'


async def exchange_managed_identity(session_id: str) -> ManagedGoogleIdentity:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            result = await client.get(SESSION_DATA_URL, headers={'X-Session-ID': session_id})
        if result.status_code in (400, 401, 403, 404):
            raise HTTPException(400, 'Google sign-in expired or was cancelled. Please start again.')
        if result.status_code != 200 or len(result.content) > 32768:
            raise HTTPException(502, 'Google sign-in is temporarily unavailable. Please try again.')
        identity = ManagedGoogleIdentity.model_validate(result.json())
    except (httpx.HTTPError, ValidationError, ValueError):
        # Never include headers, provider bodies, identifiers or credentials in logs/errors.
        raise HTTPException(502, 'Google sign-in could not be verified. Please start again.') from None
    if identity.email_verified is False:
        raise HTTPException(403, 'Please use a verified Google email address.')
    return identity


def identity_key(identity: ManagedGoogleIdentity):
    return digest('emergent-google:' + identity.id)


async def _mapped_user(identity: ManagedGoogleIdentity):
    binding = await db.oauth_identities.find_one({'_id': identity_key(identity)})
    if not binding:
        return None
    user = await db.users.find_one({'id': binding['user_id']}, {'_id': 0})
    if not user or user.get('is_guest'):
        raise HTTPException(403, 'This Google connection needs account support. No records were changed.')
    return user


async def resolve_google_user(identity: ManagedGoogleIdentity, password: str | None = None):
    """Return None when linking needs a password or explicit operator-approved recovery."""
    email = str(identity.email).strip().lower()
    async with lease('google-account:' + digest(email), 30):
        mapped = await _mapped_user(identity)
        if mapped:
            return mapped
        user = await db.users.find_one({'email': email}, {'_id': 0})
        if not user:
            profile = UserProfile(name=(identity.name.strip() or 'Sales professional')[:80])
            user = {**profile.model_dump(), 'email': email, 'is_guest': False,
                    'email_verified': identity.email_verified is True, 'created_via': 'emergent_google'}
            try:
                await db.users.insert_one(dict(user))
            except DuplicateKeyError:
                # A password signup may win the unique-email race. It must pass linking rules.
                user = await db.users.find_one({'email': email}, {'_id': 0})
                if not user:
                    raise HTTPException(409, 'Sign-in is processing. Please try again.') from None
            else:
                # New identity owns its newly created personal account; no old records to merge.
                await _bind(identity, user['id'])
                return await personal_workspace(user)
        if user.get('is_guest'):
            raise HTTPException(409, 'This account cannot be linked automatically.')
        other_binding = await db.oauth_identities.find_one({'user_id': user['id']})
        if other_binding and other_binding['_id'] != identity_key(identity):
            raise HTTPException(409, 'Use the Google account already connected to this RepForge account.')
        if identity.email_verified is not True:
            if not password:
                return None
            if len(password.encode('utf-8')) > 72 or not verify_password(password, user.get('password', '')):
                raise HTTPException(400, 'That RepForge password did not match. Please try again.')
        await _bind(identity, user['id'])
        # Preserve name, password, workspace, memberships, roles, XP and transcripts.
        return await personal_workspace(user)


async def _bind(identity: ManagedGoogleIdentity, user_id: str):
    try:
        await db.oauth_identities.update_one({'_id': identity_key(identity)}, {'$setOnInsert': {
            'provider': 'emergent_google', 'user_id': user_id, 'created_at': datetime.now(timezone.utc),
        }}, upsert=True)
    except DuplicateKeyError:
        raise HTTPException(409, 'This account already has a Google connection.') from None
    bound = await db.oauth_identities.find_one({'_id': identity_key(identity)})
    if bound['user_id'] != user_id:
        raise HTTPException(409, 'This Google connection belongs to another account.')


async def finish_google_session(flow: dict, user: dict, response: Response):
    async with data_operation(user['id']):
        return await _finish_google_session(flow, user, response)


async def _finish_google_session(flow: dict, user: dict, response: Response):
    epoch = user.get('auth_epoch', 0)
    if flow.get('status') == 'completed' and flow.get('auth_epoch') != epoch:
        raise HTTPException(400, 'This sign-in was revoked. Please start Google sign-in again.')
    user = await personal_workspace(user)
    # Existing RepForge session issuer/revocation policy; no unused upstream session token stored.
    token = await issue_session(response, user['id'])
    await db.oauth_flows.update_one({'_id': flow['_id']}, {'$set': {
        'status': 'completed', 'user_id': user['id'], 'auth_epoch': epoch,
    }, '$unset': {'identity': ''}})
    return GoogleExchangeResponse(status='authenticated', session=SessionResponse(user=UserProfile(**user), token=token))