"""Atomic per-user starts; all paid creation paths share one lease and budget."""
from functools import wraps
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from lib.db import db
from lib.security import lease, rate_limit


def guarded_start(fn):
    @wraps(fn)
    async def wrapped(*args, **kwargs):
        me = kwargs['me']
        async with lease(f'start:{me["id"]}', 150):
            await rate_limit(f'start:{me["id"]}', 8 if me.get('is_guest') else 40, 3600,
                             'Practice start allowance reached. Please return later.')
            if me.get('is_guest'):
                await rate_limit(f'guest-lifetime:{me["id"]}', 12, 86400 * 30, 'Guest demo allowance reached. Create an account for more practice.')
            await db.simulations.update_many({'user_id': me['id'], 'status': {'$in': ['preparation', 'active']},
                'started_at': {'$lt': datetime.now(timezone.utc) - timedelta(hours=3)}}, {'$set': {'status': 'abandoned'}})
            count = await db.simulations.count_documents({'user_id': me['id'], 'status': {'$in': ['preparation', 'active', 'ending', 'grading', 'analyzing']}})
            if count >= 3:
                raise HTTPException(409, 'You have three open calls. Resume or abandon one from History.')
            return await fn(*args, **kwargs)
    return wrapped