"""Provider failures and races are mocked; no paid calls."""
import asyncio
import pytest
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from lib.db import db
from lib.recovery import recover_once
from models.schemas import Simulation, TranscriptTurn, TurnRequest, Evaluation
from routers.simulations import add_turn, complete_simulation, activate


@pytest.mark.asyncio(loop_scope='session')
async def test_lifecycle_regressions():
    await cases()


async def cases():
    uid = 'internal-lifecycle-' + str(uuid.uuid4())
    me = {'id': uid, 'is_internal': True, 'workspace_id': uid}
    await db.users.insert_one({**me, 'name': 'Internal lifecycle', 'xp': 0})
    from lib.catalog import scenario_by_id
    sim = Simulation(user_id=uid, exercise_id='cold-call', exercise_name='Cold Call', difficulty=2,
        difficulty_name='Developing', scenario=scenario_by_id('crm-vp-sales'),
        transcript=[TranscriptTurn(speaker='prospect', text='Hello?')])
    await db.simulations.insert_one(sim.model_dump())
    try:
        await activate(sim.id, me)
        entered, release = asyncio.Event(), asyncio.Event()
        async def reply(*args):
            entered.set()
            await release.wait()
            return 'Late reply'
        captured = []
        async def grade(stored, transcript, duration):
            captured.extend(transcript)
            return Evaluation(overall_score=65, headline='Controlled grade')
        with patch('routers.simulations._prospect_reply', reply), patch('routers.simulations._grade', grade):
            task = asyncio.create_task(add_turn(sim.id, TurnRequest(text='Have you got a minute?', idempotency_key='race-turn-key'), me))
            await entered.wait()
            completed = await complete_simulation(sim.id, me)
            release.set()
            try:
                await task
                assert False
            except HTTPException as e:
                assert e.status_code == 409
            saved = await db.simulations.find_one({'id': sim.id})
            assert saved['transcript'] == saved['frozen_transcript'] == captured
            assert len(captured) == 2
            await complete_simulation(sim.id, me)
            user = await db.users.find_one({'id': uid})
            assert user['xp'] == completed.xp_awarded
            assert user['award_ids'] == [sim.id]
        sim2 = sim.model_copy(update={'id': str(uuid.uuid4()), 'status': 'active'})
        await db.simulations.insert_one(sim2.model_dump())
        payload = TurnRequest(text='What gets in the way?', idempotency_key='durable-retry-key')
        with patch('routers.simulations._prospect_reply', AsyncMock(side_effect=RuntimeError('mocked failure'))):
            try:
                await add_turn(sim2.id, payload, me)
            except HTTPException as e:
                assert e.status_code == 502
        assert len((await db.simulations.find_one({'id': sim2.id}))['transcript']) == 2
        with patch('routers.simulations._prospect_reply', AsyncMock(return_value='Disconnected systems.')) as provider:
            first = await add_turn(sim2.id, payload, me)
            again = await add_turn(sim2.id, payload, me)
            assert len(first.transcript) == len(again.transcript) == 3
            assert provider.await_count == 1
        with patch('routers.simulations._grade', AsyncMock(side_effect=HTTPException(502, 'MOCKED grading failure'))):
            try:
                await complete_simulation(sim2.id, me)
            except HTTPException:
                pass
        failed = await db.simulations.find_one({'id': sim2.id})
        assert failed['status'] == 'grading_failed' and failed['frozen_transcript'] == failed['transcript']
        try:
            await add_turn(sim2.id, TurnRequest(text='Not allowed now'), me)
            assert False
        except HTTPException as e:
            assert e.status_code == 409
        await db.simulations.update_one({'id': sim2.id}, {'$set': {'status': 'grading', 'grading_deadline': datetime.now(timezone.utc) - timedelta(seconds=1)}})
        await recover_once()
        assert (await db.simulations.find_one({'id': sim2.id}))['status'] == 'grading_failed'
        print('PASS: frozen pending-turn race, durable speech failure, duplicate-turn retry, XP once, grading failure and worker recovery')
    finally:
        await db.users.delete_one({'id': uid})
        await db.simulations.delete_many({'user_id': uid})