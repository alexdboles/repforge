"""Recover durable grading state and idempotent reward outbox after worker loss."""
import asyncio
import logging
from datetime import datetime, timezone
from lib.db import db


async def recover_once():
    now = datetime.now(timezone.utc)
    await db.simulations.update_many({'status': {'$in': ['grading', 'analyzing']}, '$or': [
        {'grading_deadline': {'$lt': now}}, {'grading_deadline': {'$exists': False}}]}, [{'$set': {
            'status': 'grading_failed', 'grading_error': 'Grading was interrupted. Retry to recover your saved call.',
            'frozen_transcript': {'$ifNull': ['$frozen_transcript', '$transcript']},
            'frozen_version': {'$ifNull': ['$frozen_version', {'$ifNull': ['$version', 0]}]},
            'ended_at': {'$ifNull': ['$ended_at', now]},
        }}])
    from routers.simulations import _commit_rewards
    async for sim in db.simulations.find({'status': 'completed', 'rewards_pending': True}):
        await _commit_rewards(sim)


async def recovery_loop():
    while True:
        try:
            await recover_once()
        except Exception:
            logging.getLogger(__name__).warning('Recovery will retry on next sweep')
        await asyncio.sleep(30)