"""One-use email recovery; responses do not reveal account membership."""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from lib.db import db
from lib.auth import hash_password
from lib.data_guard import data_operation
from lib.security import digest, rate_limit, client_address
from lib.mail import recovery_configured, send_reset

router = APIRouter(prefix='/auth', tags=['auth'])


class Forgot(BaseModel):
    email: EmailStr = Field(max_length=254)


class Reset(BaseModel):
    token: str = Field(min_length=40, max_length=128)
    password: str = Field(min_length=8, max_length=72)


async def deliver_reset(uid, email):
    token = secrets.token_urlsafe(32)
    token_hash = digest(token)
    try:
        async with data_operation(uid):
            await db.users.update_one({'id': uid}, {'$set': {
                'password_reset_hash': token_hash,
                'password_reset_expires': datetime.now(timezone.utc) + timedelta(minutes=30)}})
            try:
                await send_reset(email, token)
            except Exception:
                await db.users.update_one({'id': uid, 'password_reset_hash': token_hash},
                    {'$unset': {'password_reset_hash': '', 'password_reset_expires': ''}})
                raise
    except Exception:
        # No email, proof, provider body or credential is written to logs.
        logging.getLogger(__name__).error('Password recovery delivery failed')


@router.post('/forgot-password', status_code=202)
async def forgot(payload: Forgot, request: Request, tasks: BackgroundTasks):
    if not recovery_configured():
        raise HTTPException(503, 'Email recovery is not available yet. Please contact support.')
    email = str(payload.email).strip().lower()
    await rate_limit('reset-peer:' + client_address(request), 10, 3600, 'Please wait before requesting another reset.')
    await rate_limit('reset-address:' + digest(email), 3, 3600, 'Please wait before requesting another reset.')
    user = await db.users.find_one({'email': email, 'is_guest': {'$ne': True}}, {'id': 1})
    if user:
        tasks.add_task(deliver_reset, user['id'], email)
    return {'message': 'If an account matches that address, a reset link will arrive shortly. Check your spam folder too.'}


@router.post('/reset-password')
async def reset(payload: Reset, request: Request):
    await rate_limit('reset-attempt:' + client_address(request), 20, 300, 'Too many attempts. Please wait.')
    query = {'password_reset_hash': digest(payload.token), 'password_reset_expires': {'$gt': datetime.now(timezone.utc)}}
    user = await db.users.find_one(query, {'id': 1})
    if not user:
        raise HTTPException(400, 'This reset link is invalid or expired. Request a new one.')
    hashed = hash_password(payload.password)
    async with data_operation(user['id']):
        result = await db.users.update_one({**query, 'id': user['id']}, {
            '$set': {'password': hashed}, '$inc': {'auth_epoch': 1},
            '$unset': {'password_reset_hash': '', 'password_reset_expires': ''}})
        if not result.modified_count:
            raise HTTPException(400, 'This reset link is invalid or expired. Request a new one.')
    return {'message': 'Password updated. Sign in with your new password. Previous sessions have been signed out.'}
