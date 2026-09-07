"""Shared Mongo budgets and expiring cross-worker leases."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import ipaddress
import os
import time
import uuid
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from lib.db import db


async def rate_limit(key: str, limit: int, window_seconds: int, message: str, cost: int = 1):
    now = time.time()
    bucket = f'{key}:{int(now // window_seconds)}'
    doc = await db.rate_limits.find_one_and_update({'_id': bucket}, {
        '$inc': {'count': cost}, '$setOnInsert': {
            'expires_at': datetime.fromtimestamp((int(now // window_seconds) + 1) * window_seconds, timezone.utc)
        }}, upsert=True, return_document=ReturnDocument.AFTER)
    if doc['count'] > limit:
        raise HTTPException(429, message)


async def provider_budget(kind: str, cost: int = 1):
    # Conservative reservation ceilings, not exact currency-spend claims.
    limits = {'llm': int(os.environ.get('DAILY_LLM_REQUEST_LIMIT', '1200')),
              'tts': int(os.environ.get('DAILY_TTS_CHARACTER_LIMIT', '150000'))}
    await rate_limit(f'provider:{kind}', limits[kind], 86400,
                     'Today’s shared practice allowance is used. Please return later.', cost)


def client_address(request):
    peer = request.client.host if request.client else 'unknown'
    networks = os.environ.get('TRUSTED_PROXY_CIDRS', '').split(',')
    try:
        trusted = lambda addr: any(n.strip() and ipaddress.ip_address(addr) in ipaddress.ip_network(n.strip()) for n in networks)
        if trusted(peer):
            chain = [x.strip() for x in request.headers.get('x-forwarded-for', '').split(',') if x.strip()] + [peer]
            for addr in reversed(chain):
                if not trusted(addr):
                    return addr
    except ValueError:
        pass
    return peer


@asynccontextmanager
async def lease(key: str, seconds: int = 150):
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    try:
        doc = await db.leases.find_one_and_update(
            {'_id': key, 'expires_at': {'$lte': now}},
            {'$set': {'token': token, 'expires_at': now + timedelta(seconds=seconds)}},
            upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        raise HTTPException(409, 'Another request is still processing. Please wait.') from None
    try:
        yield doc
    finally:
        await db.leases.delete_one({'_id': key, 'token': token})


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


async def ensure_indexes():
    await db.users.create_index('id', unique=True)
    await db.users.create_index('email', unique=True, partialFilterExpression={'email': {'$type': 'string'}})
    await db.memberships.create_index([('workspace_id', 1), ('user_id', 1)], unique=True)
    await db.simulations.create_index('id', unique=True)
    await db.simulations.create_index([('user_id', 1), ('status', 1), ('started_at', -1)])
    await db.assignments.create_index([('workspace_id', 1), ('status', 1)])
    await db.evidence_events.create_index([('excluded', 1), ('at', 1), ('event', 1)])
    for collection in ('rate_limits', 'leases', 'audio_cache', 'invitations'):
        await db[collection].create_index('expires_at', expireAfterSeconds=0)