"""Explicit ownership inventory. No collection-wide deletion and no soft-delete success."""
from datetime import datetime, timezone
import math
import re
import json
from contextlib import AsyncExitStack
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from lib.db import db
from lib.data_guard import exclusive_data
from lib.security import digest, lease
from models.privacy import DataExport, DeletionResult

OWNED = ('simulations', 'sales_profiles', 'custom_scenarios', 'assignments', 'memberships', 'oauth_identities', 'oauth_recoveries')
SECRET_FIELDS = {'password_reset_hash', 'password_reset_expires', '_id', 'password', 'password_hash', 'auth_epoch', 'token', 'session_token', 'access_token',
    'refresh_token', 'verifier_hash', 'code_hash', 'flow_id', 'grading_token', 'failed_turn_key', 'request_key',
    'data_operations', 'privacy_lock', 'award_ids', 'is_admin', 'is_internal'}
LIMITS = [
    'Passwords, credential hashes, session tokens, sign-in proofs and internal lock identifiers are excluded.',
    'Other people’s workspace records and invitation addresses are excluded.',
    'Raw microphone recordings are not stored by RepForge. Binary AI voice cache and infrastructure logs/backups are not in this JSON.',
    'Provider-held copies are governed by the provider; this export and deletion cannot retrieve or erase them.',
]


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in SECRET_FIELDS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.isoformat()
    return value


async def selectors(user):
    uid = user['id']
    sims = await db.simulations.distinct('id', {'user_id': uid})
    flows = {'$or': [{'user_id': uid}, {'link_user_id': uid}]}
    if user.get('email'):
        flows['$or'].append({'identity.email': user['email']})
    flow_ids = await db.oauth_flows.distinct('_id', flows)
    return {**{name: {'user_id': uid} for name in OWNED}, 'users': {'id': uid},
        'workspaces': {'owner_id': uid}, 'oauth_flows': flows, 'oauth_codes': {'flow_id': {'$in': flow_ids}},
        'evidence_events': {'$or': [{'actor': digest(uid)}, {'simulation_id': {'$in': sims}}]},
        'feedback': {'_id': {'$in': sims}}, 'audio_cache': await audio_selector(user)}


async def audio_selector(user):
    # Legacy cache keys predate user_id metadata. Reconstruct only this user's
    # keys from saved prospect turns/sample text; never erase another user's cache.
    from routers.voice import _delivery, MODEL_ID
    from lib.voicecast import snapshot
    keys = []
    async for sim in db.simulations.find({'user_id': user['id']}):
        voice = sim.get('voice_config') or snapshot(sim['scenario'], sim.get('voice_persona', 'default'))
        texts = [t['text'] for t in sim.get('transcript', []) if t.get('speaker') == 'prospect']
        texts.append(f"Hello, this is {sim['scenario']['prospect_name'].split()[0]}. Can you hear me?")
        for text in texts:
            keys.append(digest(json.dumps([user['id'], voice, text, _delivery(voice, sim['difficulty']), MODEL_ID], sort_keys=True)))
    return {'$or': [{'user_id': user['id']}, {'_id': {'$in': keys}}]}


async def export_data(user):
    queries = await selectors(user)
    result = {}
    for name, query in queries.items():
        if name in ('oauth_codes', 'audio_cache'):
            continue
        rows = await db[name].find(query).to_list(None)
        # Only this person's membership/ownership metadata, never a team roster.
        result[name] = [clean(row) for row in rows]
        if name == 'feedback':
            for row, stored in zip(result[name], rows):
                row['simulation_id'] = stored['_id']
        if name == 'oauth_recoveries':
            for row, stored in zip(result[name], rows):
                row['reference'] = stored['_id']
    result['invitations'] = [clean(row) for row in await db.invitations.find(
        {'email': user['email']} if user.get('email') else {'accepted_by': user['id']}).to_list(None)]
    for row in result['assignments']:
        if row.get('assigned_by') != user['id']:
            row.pop('assigned_by', None)
    for row in result['invitations']:
        if row.get('created_by') != user['id']:
            row.pop('created_by', None)
    return DataExport(exported_at=datetime.now(timezone.utc), user_id=user['id'], data=jsonable_encoder(result), exclusions=LIMITS)


async def delete_account(user, scope='account'):
    uid = user['id']
    async with AsyncExitStack() as stack:
        # Resolve/link and delete cannot race over the same verified email.
        if user.get('email'):
            await stack.enter_async_context(lease('google-account:' + digest(user['email']), 150))
        await stack.enter_async_context(exclusive_data(uid))
        queries = await selectors(user)
        for flow_id in await db.oauth_flows.distinct('_id', queries['oauth_flows']):
            await stack.enter_async_context(lease('google-flow:' + flow_id, 150))
        counts = {}
        # Delete dependants before primary user. A failure is an error, not success;
        # the user stays signable and repeating the operation finishes remaining work.
        for name, query in queries.items():
            if name in ('users', 'workspaces'):
                continue
            counts[name] = (await db[name].delete_many(query)).deleted_count
        invite_terms = [{'created_by': uid}, {'accepted_by': uid}]
        if user.get('email'):
            invite_terms.append({'email': user['email']})
        counts['invitations'] = (await db.invitations.delete_many({'$or': invite_terms})).deleted_count
        # Assignments owned by other people remain, but lose the deleted assigner's ID.
        await db.assignments.update_many({'assigned_by': uid}, {'$set': {'assigned_by': 'Deleted account'}})
        counts['workspaces'] = 0
        async for workspace in db.workspaces.find({'owner_id': uid}):
            if await db.memberships.count_documents({'workspace_id': workspace['id']}):
                await db.workspaces.update_one({'id': workspace['id']}, {'$unset': {'owner_id': ''}})
            else:
                counts['workspaces'] += (await db.workspaces.delete_one({'id': workspace['id']})).deleted_count
        counts['rate_limits'] = (await db.rate_limits.delete_many({'_id': {'$regex': ':' + re.escape(uid) + ':'}})).deleted_count
        counts['users'] = (await db.users.delete_one({'id': uid})).deleted_count
        return DeletionResult(scope=scope, counts=counts, message='Your RepForge data was permanently deleted from the active database. Provider copies, infrastructure logs and private backups are not erased by this action.')


async def delete_simulation(user, sim_id):
    uid = user['id']
    async with exclusive_data(uid):
        source = await db.simulations.find_one({'id': sim_id, 'user_id': uid})
        if not source:
            raise HTTPException(404, 'Session not found')
        # Full retries and moment drills contain copied quotes and scenario context.
        # Remove the owned descendants too, rather than hiding a source row only.
        ids = {sim_id}
        while True:
            children = set(await db.simulations.distinct('id', {'user_id': uid, 'retry_of': {'$in': list(ids)}})) - ids
            if not children:
                break
            ids.update(children)
        deleted_sims = await db.simulations.find({'id': {'$in': list(ids)}, 'user_id': uid}).to_list(None)
        audio_query = await audio_selector(user)
        counts = {'simulations': (await db.simulations.delete_many({'id': {'$in': list(ids)}, 'user_id': uid})).deleted_count}
        counts['feedback'] = (await db.feedback.delete_many({'_id': {'$in': list(ids)}})).deleted_count
        counts['evidence_events'] = (await db.evidence_events.delete_many({'simulation_id': {'$in': list(ids)}, 'actor': digest(uid)})).deleted_count
        # Cache can be shared between this person's calls. Clearing all of their AI
        # audio avoids keeping copied utterances; other people’s caches are untouched.
        counts['audio_cache'] = (await db.audio_cache.delete_many(audio_query)).deleted_count
        await db.assignments.update_many({'user_id': uid, 'completed_simulation_id': {'$in': list(ids)}},
            {'$set': {'status': 'pending', 'completed_at': None, 'completed_simulation_id': None, 'score': None}})
        # Earlier-call memory is a derived copy; invalidate it on remaining calls.
        await db.simulations.update_many({'user_id': uid}, {'$set': {'prior_context': ''}})
        fresh = await db.users.find_one({'id': uid}) or {}
        xp = max(0, fresh.get('xp', 0) - sum(s.get('xp_awarded', 0) for s in deleted_sims))
        await db.users.update_one({'id': uid}, {'$set': {'xp': xp, 'level': 1 + math.isqrt(xp // 250),
            'badges': [], 'streak': 0, 'last_practice_date': None,
            'moments_corrected': max(0, fresh.get('moments_corrected', 0) - sum(1 for s in deleted_sims if s.get('moment_improved') is True))}, '$pull': {'award_ids': {'$in': list(ids)}}})
        return DeletionResult(scope='session', counts=counts, message='Session and linked retries permanently deleted. Derived memory and streak reset; earned XP from deleted calls removed.')