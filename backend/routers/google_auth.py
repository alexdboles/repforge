import hmac
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Request, Response
from pymongo.errors import DuplicateKeyError
from lib.db import db
from lib.data_guard import data_operation
from lib.security import digest, lease, rate_limit, client_address
from lib.google_auth import exchange_managed_identity, resolve_google_user, finish_google_session
from models.google_auth import (GoogleStartResponse, GoogleFlowProof, GoogleExchangeRequest,
    GoogleLinkRequest, GoogleExchangeResponse, ManagedGoogleIdentity, GoogleRecoveryResponse)

router = APIRouter(prefix='/auth/google', tags=['auth'])


@router.post('/start', response_model=GoogleStartResponse)
async def start(request: Request):
    await rate_limit('google-start:' + client_address(request), 30, 3600, 'Too many Google sign-in attempts. Please try later.')
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.oauth_flows.insert_one({'_id': digest(state), 'verifier_hash': digest(verifier),
        'status': 'pending', 'expires_at': expiry})
    return GoogleStartResponse(state=state, verifier=verifier, expires_at=expiry)


async def load_flow(payload: GoogleFlowProof):
    flow = await db.oauth_flows.find_one({'_id': digest(payload.state), 'expires_at': {'$gt': datetime.now(timezone.utc)}})
    if not flow or not hmac.compare_digest(flow['verifier_hash'], digest(payload.verifier)):
        raise HTTPException(400, 'This Google sign-in was not started in this tab, or has expired. Please start again.')
    return flow


async def completed(flow, response):
    user = await db.users.find_one({'id': flow.get('user_id')}, {'_id': 0})
    if not user:
        raise HTTPException(400, 'This sign-in is no longer available. Please start again.')
    return await finish_google_session(flow, user, response)


@router.post('/exchange', response_model=GoogleExchangeResponse)
async def exchange(payload: GoogleExchangeRequest, request: Request, response: Response):
    await rate_limit('google-exchange:' + client_address(request), 60, 3600, 'Too many Google sign-in attempts. Please try later.')
    async with lease('google-flow:' + digest(payload.state), 30):
        flow = await load_flow(payload)
        code_hash = digest(payload.session_id)
        if flow.get('code_hash') and flow['code_hash'] != code_hash:
            raise HTTPException(400, 'The Google sign-in response does not match this attempt.')
        if flow['status'] == 'completed':
            return await completed(flow, response)
        if flow.get('identity'):
            identity = ManagedGoogleIdentity.model_validate(flow['identity'])
        else:
            # A provider code cannot be exchanged under another independently created flow.
            try:
                await db.oauth_codes.update_one({'_id': code_hash}, {'$setOnInsert': {
                    'flow_id': flow['_id'], 'expires_at': datetime.now(timezone.utc) + timedelta(days=1),
                }}, upsert=True)
            except DuplicateKeyError:
                pass
            code = await db.oauth_codes.find_one({'_id': code_hash})
            if code['flow_id'] != flow['_id']:
                raise HTTPException(400, 'This Google sign-in response has already been used. Please start again.')
            identity = await exchange_managed_identity(payload.session_id)
            await db.oauth_flows.update_one({'_id': flow['_id']}, {'$set': {
                'identity': identity.model_dump(mode='json'), 'code_hash': code_hash,
            }})
        user = await resolve_google_user(identity)
        if user is None:
            email = str(identity.email).strip().lower()
            target = await db.users.find_one({'email': email}, {'id': 1, 'password': 1})
            if not target:
                raise HTTPException(409, 'The existing account changed. Please restart Google sign-in.')
            await db.oauth_flows.update_one({'_id': flow['_id']}, {'$set': {'status': 'link_required', 'link_user_id': target['id']}})
            return GoogleExchangeResponse(status='link_required', email=email, password_available=bool(target.get('password')))
        return await finish_google_session(flow, user, response)


@router.post('/recovery', response_model=GoogleRecoveryResponse)
async def request_recovery(payload: GoogleFlowProof, request: Request):
    """Save an ownership-review request, never silently link or reset a password."""
    await rate_limit('google-recovery:' + client_address(request), 10, 3600,
                     'Too many recovery requests. Please try again later.')
    async with lease('google-flow:' + digest(payload.state), 30):
        flow = await load_flow(payload)
        if flow['status'] != 'link_required' or not flow.get('identity'):
            raise HTTPException(400, 'Restart Google sign-in before requesting an account connection.')
        if flow.get('recovery_reference'):
            existing = await db.oauth_recoveries.find_one({'_id': flow['recovery_reference'], 'expires_at': {'$gt': datetime.now(timezone.utc)}})
            if existing:
                return GoogleRecoveryResponse(reference=existing['_id'], status=existing['status'], expires_at=existing['expires_at'])
        identity = ManagedGoogleIdentity.model_validate(flow['identity'])
        target = await db.users.find_one({'email': str(identity.email).lower()}, {'id': 1})
        if not target or (flow.get('link_user_id') and target['id'] != flow['link_user_id']):
            raise HTTPException(409, 'The existing account changed. Please restart Google sign-in.')
        reference = 'RF-' + secrets.token_hex(12)
        expiry = datetime.now(timezone.utc) + timedelta(days=3)
        async with data_operation(target['id']):
            await db.oauth_recoveries.insert_one({'_id': reference, 'user_id': target['id'],
                'identity': identity.model_dump(mode='json'), 'status': 'pending',
                'created_at': datetime.now(timezone.utc), 'expires_at': expiry})
        await db.oauth_flows.update_one({'_id': flow['_id']}, {'$set': {'recovery_reference': reference}})
        return GoogleRecoveryResponse(reference=reference, status='pending', expires_at=expiry)


@router.post('/link', response_model=GoogleExchangeResponse)
async def link(payload: GoogleLinkRequest, request: Request, response: Response):
    await rate_limit('google-link-peer:' + client_address(request), 20, 300, 'Too many password attempts. Please wait a few minutes.')
    async with lease('google-flow:' + digest(payload.state), 30):
        flow = await load_flow(payload)
        if flow['status'] == 'completed':
            return await completed(flow, response)
        if flow['status'] != 'link_required' or not flow.get('identity'):
            raise HTTPException(400, 'Complete Google sign-in before connecting an existing account.')
        identity = ManagedGoogleIdentity.model_validate(flow['identity'])
        await rate_limit('google-link-account:' + digest(str(identity.email).lower()), 10, 600,
                         'Too many password attempts. Please wait before trying again.')
        user = await resolve_google_user(identity, payload.password)
        if not user:
            raise HTTPException(400, 'The existing account could not be verified.')
        return await finish_google_session(flow, user, response)