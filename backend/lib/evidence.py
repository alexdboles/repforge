"""Server-authored minimal events. Never store transcript text, names, email or credentials."""
from datetime import datetime, timezone
import hashlib
from lib.db import db

EVENTS = {'demo_started', 'practice_started', 'first_reply', 'grading_completed', 'retry_started', 'retry_completed', 'comparable_improvement'}


async def record_event(name: str, sim: dict):
    if name not in EVENTS:
        raise ValueError('Unknown event')
    user = await db.users.find_one({'id': sim['user_id']}, {'email': 1, 'is_internal': 1}) or {}
    # Historical fixture identities are not customers. No retroactive adoption reconstruction.
    email = user.get('email', '').lower()
    excluded = bool(user.get('is_internal') or email in ('judge@repforge.dev', 'alice@example.com', 'bob@example.com') or email.endswith(('.test', '@example.com')))
    actor = hashlib.sha256(sim['user_id'].encode()).hexdigest()
    now = datetime.now(timezone.utc)
    await db.evidence_events.update_one({'_id': f"{sim['id']}:{name}"}, {'$setOnInsert': {
        'event': name, 'actor': actor, 'simulation_id': sim['id'], 'at': now,
        'day': now.date().isoformat(), 'excluded': excluded, 'is_demo': sim.get('is_demo', False),
        'mode': sim.get('mode', 'guided'), 'exercise_id': sim['exercise_id'], 'difficulty': sim['difficulty'],
        'assisted': sim.get('assisted', False), 'schema_version': 1,
    }}, upsert=True)