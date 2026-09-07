import asyncio
from datetime import date, datetime, timezone
import uuid
import pytest
from fastapi import HTTPException
from lib.db import db
from lib.evidence import record_event
from routers.evidence import summary, feedback
from models.evidence import FeedbackRequest


@pytest.mark.asyncio(loop_scope='session')
async def test_owner_and_evidence_privacy():
    await cases()


async def cases():
    uid = 'internal-evidence-' + str(uuid.uuid4())
    sim = {'id': uid, 'user_id': uid, 'exercise_id': 'cold-call', 'difficulty': 2, 'is_demo': True, 'status': 'completed'}
    await db.users.insert_one({'id': uid, 'is_internal': True})
    await db.simulations.insert_one(sim)
    try:
        await record_event('demo_started', sim)
        await record_event('demo_started', sim)
        await record_event('practice_started', sim)
        row = await db.evidence_events.find_one({'_id': f'{uid}:demo_started'})
        assert row['excluded'] is True
        assert not {'text', 'transcript', 'email', 'name', 'token', 'password'} & row.keys()
        assert await db.evidence_events.count_documents({'_id': f'{uid}:demo_started'}) == 1
        with pytest.raises(HTTPException) as denied:
            await summary(me={'id': uid, 'workspace_role': 'owner'})
        assert denied.value.status_code == 403
        # No events are backfilled as adoption; this controlled test reads a future empty range.
        result = await summary(start=date(2030, 1, 1), end=date(2030, 1, 2), me={'id': uid, 'is_admin': True})
        assert result.sample_size == result.demo_starts == result.completed_grading == 0
        assert (await feedback(FeedbackRequest(simulation_id=uid, rating=4), {'id': uid, 'is_internal': True})).saved
        with pytest.raises(HTTPException):
            await feedback(FeedbackRequest(simulation_id=uid, rating=5), {'id': 'other'})
    finally:
        await db.users.delete_one({'id': uid})
        await db.simulations.delete_one({'id': uid})
        await db.evidence_events.delete_many({'simulation_id': uid})
        await db.feedback.delete_one({'_id': uid})