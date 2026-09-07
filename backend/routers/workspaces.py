"""Invitation possession + matching authenticated email, never organisation text."""
from datetime import datetime, timezone, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from lib.auth import current_user, require_manager
from lib.db import db
from lib.security import digest, rate_limit
from models.schemas import InvitationCreate, InvitationResponse, InvitationAccept, UserProfile

router = APIRouter(tags=['workspaces'])


@router.post('/workspace/invitations', response_model=InvitationResponse)
async def invite(payload: InvitationCreate, me: dict = Depends(current_user)):
    require_manager(me)
    await rate_limit(f'invite:{me["id"]}', 30, 3600, 'Invitation limit reached')
    if payload.role == 'manager' and me['workspace_role'] not in ('owner', 'admin'):
        raise HTTPException(403, 'Only workspace owners or admins may invite managers')
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=2)
    await db.invitations.insert_one({'_id': digest(token), 'email': payload.email.strip().lower(),
        'workspace_id': me['workspace_id'], 'role': payload.role, 'expires_at': expires, 'created_by': me['id']})
    return InvitationResponse(token=token, expires_at=expires)


@router.post('/workspace/join', response_model=UserProfile)
async def join(payload: InvitationAccept, me: dict = Depends(current_user)):
    if me.get('is_guest') or not me.get('email'):
        raise HTTPException(403, 'Sign in with the invited email address first')
    await rate_limit(f'join:{me["id"]}', 20, 3600, 'Too many invitation attempts')
    invite = await db.invitations.find_one_and_update({'_id': digest(payload.token),
        'email': me['email'], 'expires_at': {'$gt': datetime.now(timezone.utc)},
        '$or': [{'accepted_by': {'$exists': False}}, {'accepted_by': me['id']}]},
        {'$set': {'accepted_by': me['id']}}, return_document=ReturnDocument.AFTER)
    if not invite:
        raise HTTPException(404, 'Invitation invalid, expired or addressed to another email')
    await db.memberships.update_one({'workspace_id': invite['workspace_id'], 'user_id': me['id']},
        {'$set': {'verified': True, 'role': invite['role'], 'source': 'invitation'}}, upsert=True)
    await db.users.update_one({'id': me['id']}, {'$set': {'workspace_id': invite['workspace_id']}})
    return UserProfile(**{**me, 'workspace_id': invite['workspace_id'], 'workspace_role': invite['role']})


@router.post('/workspace/personal', response_model=UserProfile)
async def personal(me: dict = Depends(current_user)):
    wid = me['personal_workspace_id']
    await db.users.update_one({'id': me['id']}, {'$set': {'workspace_id': wid}})
    return UserProfile(**{**me, 'workspace_id': wid, 'workspace_role': 'owner'})