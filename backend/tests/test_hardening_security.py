"""Controlled accounts; no provider calls. All records made here are removed."""
import asyncio
import pytest
from datetime import datetime, timezone, timedelta
import uuid
import jwt
import httpx
from fastapi import Response
from lib.db import db
from lib.auth import _secret, hash_password, issue_session, current_user
from lib.security import lease, rate_limit
from server import app


@pytest.mark.asyncio(loop_scope='session')
async def test_security_regressions():
    await security_cases()


async def security_cases():
    prefix = f'hardening-{uuid.uuid4()}'
    ids = []
    emails = {}
    # Isolate this test's peer bucket without resetting/bypassing production counters.
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(prefix, 12345)), base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        try:
            sessions = []
            for i in range(4):
                client.cookies.clear()
                if i < 2:
                    email = f'{prefix}-{i}@example.test'
                    response = await client.post('/api/auth/signup', json={'name': f'Internal fixture {i}', 'email': email, 'password': 'Controlled2026!', 'org': 'Same company'})
                else:
                    response = await client.post('/api/auth/guest')
                assert response.status_code == 200, response.text
                session = response.json()
                ids.append(session['user']['id'])
                if i < 2:
                    emails[session['user']['id']] = email
                await db.users.update_one({'id': ids[-1]}, {'$set': {'is_internal': True}})
                sessions.append(session)
            assert len({s['user']['workspace_id'] for s in sessions}) == 4
            a, b = sessions[:2]
            client.cookies.clear()
            client.headers['Authorization'] = f'Bearer {a["token"]}'
            for path in (f'/api/teams/{b["user"]["workspace_id"]}', '/api/teams/Same%20company', '/api/teams/Personal'):
                assert (await client.get(path)).status_code == 403
            assert (await client.post('/api/assignments', json={'user_id': b['user']['id'], 'exercise_id': 'cold-call'})).status_code == 404
            wid = a['user']['workspace_id']
            await db.memberships.update_one({'workspace_id': wid, 'user_id': a['user']['id']}, {'$set': {'role': 'member'}})
            assert (await client.post('/api/assignments', json={'user_id': a['user']['id'], 'exercise_id': 'cold-call'})).status_code == 403
            for guest in sessions[2:]:
                client.headers['Authorization'] = f'Bearer {guest["token"]}'
                assert (await client.get('/api/teams/' + a['user']['workspace_id'])).status_code == 403
                assert (await client.get('/api/users/' + b['user']['id'] + '/dashboard')).status_code == 403
            await db.memberships.update_one({'workspace_id': wid, 'user_id': a['user']['id']}, {'$set': {'role': 'owner'}})
            client.headers['Authorization'] = f'Bearer {a["token"]}'
            invite = await client.post('/api/workspace/invitations', json={'email': emails[b['user']['id']], 'role': 'member'})
            assert invite.status_code == 200
            code = invite.json()['token']
            client.headers['Authorization'] = f'Bearer {sessions[2]["token"]}'
            assert (await client.post('/api/workspace/join', json={'token': code})).status_code == 403
            client.headers['Authorization'] = f'Bearer {b["token"]}'
            joined = await client.post('/api/workspace/join', json={'token': code})
            assert joined.status_code == 200 and joined.json()['workspace_role'] == 'member'
            assert (await client.get('/api/teams/' + wid)).status_code == 403
            client.headers['Authorization'] = f'Bearer {a["token"]}'
            assigned = await client.post('/api/assignments', json={'user_id': b['user']['id'], 'exercise_id': 'cold-call', 'assigned_by': 'spoofed-client-name', 'org': 'spoofed-org'})
            assert assigned.status_code == 200
            assert assigned.json()['assigned_by'] == a['user']['id'] and assigned.json()['workspace_id'] == wid
            client.headers['Authorization'] = f'Bearer {b["token"]}'
            assert (await client.delete('/api/assignments/' + assigned.json()['id'])).status_code == 403
            assert (await client.post('/api/workspace/personal')).json()['workspace_id'] == b['user']['workspace_id']
            client.headers['Authorization'] = f'Bearer {a["token"]}'
            response = Response()
            await issue_session(response, a['user']['id'])
            cookie = response.headers['set-cookie'].split(';')[0].split('=', 1)[1]
            expired = jwt.encode({'sub': a['user']['id'], 'exp': datetime.now(timezone.utc) - timedelta(seconds=1)}, _secret(), algorithm='HS256')
            assert (await current_user(cookie, f'Bearer {expired}'))['id'] == a['user']['id']
            assert (await client.post('/api/auth/logout')).status_code == 200
            client.cookies.clear()
            assert (await client.get('/api/auth/me')).status_code == 401
            client.headers.pop('Authorization')
            assert (await client.post('/api/status', json={'client_name': 'no-write'})).status_code == 404
            assert (await client.get('/api/health')).json() == {'status': 'ok'}
            assert (await client.post('/api/auth/guest', headers={'Origin': 'https://evil.example'})).status_code == 403
            client.headers['Authorization'] = f'Bearer {b["token"]}'
            assert (await client.post('/api/voice/speak', json={'text': 'arbitrary paid text'})).status_code == 422
            assert (await client.get('/api/voice/cast')).status_code == 403
            try:
                hash_password('😀' * 30)
                assert False
            except Exception as exc:
                assert getattr(exc, 'status_code', None) == 422
            await rate_limit(prefix, 1, 3600, 'bounded')
            try:
                await rate_limit(prefix, 1, 3600, 'bounded')
                assert False
            except Exception as exc:
                assert getattr(exc, 'status_code', None) == 429
            async with lease(prefix):
                try:
                    async with lease(prefix):
                        assert False
                except Exception as exc:
                    assert getattr(exc, 'status_code', None) == 409
            print('PASS: 4 isolated workspaces, name spoofing, assignment permissions, cookie precedence, revocation, CSRF, TTS restriction, admin QA, UTF-8 bound, shared budget and lease')
        finally:
            await db.users.delete_many({'id': {'$in': ids}})
            await db.memberships.delete_many({'user_id': {'$in': ids}})
            await db.workspaces.delete_many({'owner_id': {'$in': ids}})
            await db.assignments.delete_many({'user_id': {'$in': ids}})
            await db.invitations.delete_many({'created_by': {'$in': ids}})