"""Concurrent reads/writes may coexist; destructive requests require an idle account.

Operation markers live in the existing user document so a deleted user is never
recreated by cleanup. Five-minute stale markers cover bounded provider timeouts.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from fastapi import HTTPException
from lib.db import db


@asynccontextmanager
async def data_operation(user_id: str):
    now = datetime.now(timezone.utc)
    token = str(uuid4())
    await db.users.update_one({'id': user_id}, {'$pull': {'data_operations': {'expires_at': {'$lte': now}}}})
    result = await db.users.update_one({'id': user_id, 'privacy_lock': {'$exists': False}},
        {'$push': {'data_operations': {'id': token, 'expires_at': now + timedelta(minutes=5)}}})
    if not result.matched_count:
        raise HTTPException(409, 'Account data is being deleted or is no longer available. Please sign in again.')
    try:
        yield
    finally:
        await db.users.update_one({'id': user_id}, {'$pull': {'data_operations': {'id': token}}})


@asynccontextmanager
async def exclusive_data(user_id: str):
    token = str(uuid4())
    result = await db.users.update_one({'id': user_id, 'privacy_lock': {'$exists': False},
        'data_operations': {'$not': {'$elemMatch': {'expires_at': {'$gt': datetime.now(timezone.utc)}}}}},
        {'$set': {'privacy_lock': token}})
    if not result.matched_count:
        raise HTTPException(409, 'Another request is still processing. Wait for the call or page to finish, then retry deletion.')
    try:
        yield
    finally:
        await db.users.update_one({'id': user_id, 'privacy_lock': token}, {'$unset': {'privacy_lock': ''}})