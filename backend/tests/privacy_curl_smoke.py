"""Tier-one privacy verification: real curl requests + direct Mongo postconditions.

Creates disposable internal fixtures only. No LLM/TTS provider calls or real-user
deletions. Runs as a script from backend/, with the public preview as argv[1].
"""
import asyncio
import copy
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.db import db
from lib.catalog import scenarios_for_exercise, exercise_by_id, difficulty_by_level
from lib.security import digest
from lib.data_guard import data_operation, exclusive_data
from lib.privacy import selectors, delete_account, audio_selector
from lib.llm import prospect_system_prompt, EVAL_SYSTEM, HINT_SYSTEM
from models.schemas import Simulation, TranscriptTurn

BASE = sys.argv[1].rstrip('/')


async def call(method, path, expected=200, token=None, body=None):
    args = ['curl', '-sS', '--max-time', '45', '-X', method, BASE + '/api' + path,
            '-H', 'Origin: ' + BASE, '-w', '\n%{http_code}']
    if token:
        args += ['-H', 'Authorization: Bearer ' + token]
    if body is not None:
        args += ['-H', 'Content-Type: application/json', '--data', json.dumps(body)]
    run = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True, check=True)
    text, status = run.stdout.rsplit('\n', 1)
    data = json.loads(text)
    assert int(status) == expected, (method, path, status, data)
    print('PASS', method, path, status)
    return data


async def fixture(uid, parent=None):
    scenario = copy.deepcopy(scenarios_for_exercise('cold-call')[0])
    sim = Simulation(user_id=uid, exercise_id='cold-call', exercise_name='Cold Call', difficulty=2,
        difficulty_name='Developing', scenario=scenario, status='abandoned', retry_of=parent,
        transcript=[TranscriptTurn(speaker='prospect', text='Controlled buyer greeting', at=0),
                    TranscriptTurn(speaker='rep', text='Privacy fixture transcript only', at=1)])
    await db.simulations.insert_one(sim.model_dump())
    await db.evidence_events.insert_one({'_id': sim.id + ':privacy', 'actor': digest(uid), 'simulation_id': sim.id, 'event': 'practice_started', 'excluded': True})
    await db.feedback.insert_one({'_id': sim.id, 'rating': 5})
    return sim.id


async def main():
    accounts = []
    try:
        missing = await call('GET', '/data/export', 401)
        assert 'detail' in missing
        guest = await call('POST', '/auth/guest')
        accounts.append(guest['user']['id'])
        signup = await call('POST', '/auth/signup', body={'email': f'privacy-{uuid4()}@example.test',
            'name': 'Internal Privacy Fixture', 'password': 'Privacy-Only-2026!'})
        accounts.append(signup['user']['id'])
        uid, other = accounts
        token, other_token = guest['token'], signup['token']
        await db.users.update_many({'id': {'$in': accounts}}, {'$set': {'is_internal': True}})
        source = await fixture(uid)
        child = await fixture(uid, source)
        keep = await fixture(uid)
        foreign = await fixture(other)
        now = datetime.now(timezone.utc)
        for name in ('sales_profiles', 'custom_scenarios'):
            await db[name].insert_one({'id': str(uuid4()), 'user_id': uid, 'label': 'Private fixture', 'created_at': now})
        await db.assignments.insert_one({'id': str(uuid4()), 'user_id': uid, 'assigned_by': other,
            'status': 'completed', 'completed_simulation_id': source, 'score': 70})
        await db.audio_cache.insert_one({'_id': str(uuid4()), 'user_id': uid, 'audio': b'fixture', 'expires_at': now + timedelta(days=1)})
        # Legacy audio key can be erased without metadata or touching another owner.
        user = await db.users.find_one({'id': uid})
        keys = (await audio_selector(user))['$or'][1]['_id']['$in']
        await db.audio_cache.insert_one({'_id': keys[0], 'audio': b'legacy fixture', 'expires_at': now + timedelta(days=1)})
        summary = await call('GET', '/data/summary', token=token)
        assert summary['is_guest'] and summary['counts']['simulations'] == 3
        exported = await call('GET', '/data/export', token=token)
        assert exported['schema_version'] == '1.0' and exported['user_id'] == uid
        assert len(exported['data']['simulations']) == 3
        assert exported['data']['simulations'][0]['transcript'][1]['text'] == 'Privacy fixture transcript only'
        encoded = json.dumps(exported)
        for secret in ('"password"', '"auth_epoch"', '"data_operations"', '"_id"', other_token, foreign):
            assert secret not in encoded, secret
        assert 'Privacy fixture transcript only' in encoded
        assert (await call('DELETE', f'/data/sessions/{foreign}?confirm=DELETE', 404, token))['detail'] == 'Session not found'
        assert 'detail' in await call('DELETE', '/data/guest', 422, token)
        assert 'detail' in await call('DELETE', '/data/guest?confirm=DELETE', 403, other_token)
        async with data_operation(uid):
            assert 'detail' in await call('DELETE', '/data/guest?confirm=DELETE', 409, token)
        async with exclusive_data(uid):
            assert 'detail' in await call('GET', '/data/export', 409, token)
        removed = await call('DELETE', f'/data/sessions/{source}?confirm=DELETE', token=token)
        assert removed['deleted'] and removed['counts']['simulations'] == 2
        assert not await db.simulations.find_one({'id': {'$in': [source, child]}})
        assert await db.simulations.find_one({'id': keep})
        assert await db.simulations.find_one({'id': foreign})
        assert not await db.feedback.find_one({'_id': {'$in': [source, child]}})
        assert not await db.audio_cache.find_one({'_id': keys[0]})
        assert not await db.audio_cache.find_one({'user_id': uid})
        assert (await db.assignments.find_one({'user_id': uid}))['completed_simulation_id'] is None
        assert len((await call('GET', '/data/export', token=token))['data']['simulations']) == 1
        flow_id = digest('privacy-flow-' + uid)
        await db.oauth_flows.insert_one({'_id': flow_id, 'user_id': uid, 'verifier_hash': 'never-export', 'expires_at': now + timedelta(minutes=10)})
        await db.oauth_codes.insert_one({'_id': 'code-' + uid, 'flow_id': flow_id, 'expires_at': now + timedelta(days=1)})
        await db.oauth_identities.insert_one({'_id': 'binding-' + uid, 'user_id': uid, 'provider': 'controlled-fixture'})
        await db.oauth_recoveries.insert_one({'_id': 'recovery-' + uid, 'user_id': uid, 'expires_at': now + timedelta(days=3)})
        await db.invitations.insert_one({'_id': 'invite-' + uid, 'created_by': uid, 'email': 'private-other@example.test'})
        before = await selectors(await db.users.find_one({'id': uid}))
        result = await call('DELETE', '/data/guest?confirm=DELETE', token=token)
        assert result['scope'] == 'guest' and result['counts']['users'] == 1
        for name, query in before.items():
            assert not await db[name].find_one(query), name
        assert not await db.invitations.find_one({'created_by': uid})
        assert 'detail' in await call('GET', '/auth/me', 401, token)
        assert await db.users.find_one({'id': other}) and await db.simulations.find_one({'id': foreign})
        account_export = await call('GET', '/data/export', token=other_token)
        assert 'password' not in account_export['data']['users'][0]
        result = await call('DELETE', '/data/account?confirm=DELETE', token=other_token)
        assert result['scope'] == 'account' and not await db.users.find_one({'id': other})
        assert 'detail' in await call('GET', '/auth/me', 401, other_token)
        scenario = scenarios_for_exercise('cold-call')[0]
        for level in range(1, 6):
            prompt = prospect_system_prompt(scenario, exercise_by_id('cold-call'), difficulty_by_level(level))
            assert prompt.index('SAFETY EXCEPTION') < prompt.index('For ordinary sales roleplay')
            assert 'pause the sales roleplay immediately' in prompt
        assert 'NOT sales failures' in EVAL_SYSTEM and 'SAFETY EXCEPTION' in HINT_SYSTEM
        print('PASS all permanent deletion, isolation, export, stale-session and prompt-priority assertions; real Mongo confirmed')
    finally:
        for uid in accounts:
            user = await db.users.find_one({'id': uid})
            if user:
                await delete_account(user, 'guest' if user.get('is_guest') else 'account')


if __name__ == '__main__':
    asyncio.run(main())