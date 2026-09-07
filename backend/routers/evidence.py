from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from lib.auth import current_user, require_admin, require_owned
from lib.db import db
from lib.dates import today_iso
from lib.security import rate_limit
from models.evidence import FeedbackRequest, FeedbackResponse, EvidenceSummary

router = APIRouter(tags=['evidence'])


@router.post('/feedback', response_model=FeedbackResponse)
async def feedback(payload: FeedbackRequest, me: dict = Depends(current_user)):
    await rate_limit(f'feedback:{me["id"]}', 30, 3600, 'Feedback allowance reached')
    sim = await db.simulations.find_one({'id': payload.simulation_id, 'status': 'completed'})
    if not sim:
        raise HTTPException(404, 'Completed simulation not found')
    require_owned(sim, me)
    # Link only to a minimal event; rating never contains free-text private data.
    await db.feedback.update_one({'_id': sim['id']}, {'$set': {'rating': payload.rating,
        'at': datetime.now(timezone.utc), 'excluded': bool(me.get('is_internal') or me.get('email', '').endswith(('.test', '@example.com')) or me.get('email') == 'judge@repforge.dev')}}, upsert=True)
    return FeedbackResponse()


@router.get('/owner/evidence', response_model=EvidenceSummary)
async def summary(start: date | None = None, end: date | None = None, me: dict = Depends(current_user)):
    require_admin(me)
    end = end or date.fromisoformat(today_iso())
    start = start or end - timedelta(days=29)
    if start > end or (end - start).days > 366:
        raise HTTPException(422, 'Choose an ordered range of at most 366 days')
    lower = datetime.combine(start, datetime.min.time(), timezone.utc)
    upper = datetime.combine(end + timedelta(days=1), datetime.min.time(), timezone.utc)
    match = {'excluded': False, 'at': {'$gte': lower, '$lt': upper}}
    counts = await db.evidence_events.aggregate([{'$match': match}, {'$group': {'_id': '$event', 'count': {'$sum': 1}}}]).to_list(None)
    counts = {c['_id']: c['count'] for c in counts}
    actors = await db.evidence_events.aggregate([{'$match': {**match, 'event': 'practice_started'}},
        {'$group': {'_id': '$actor', 'days': {'$addToSet': '$day'}}}]).to_list(None)
    # Demo completion rate is a cohort calculation, not completions / unrelated starts.
    demos = await db.evidence_events.distinct('simulation_id', {**match, 'event': 'demo_started'})
    finished = await db.evidence_events.count_documents({'excluded': False, 'event': 'grading_completed', 'simulation_id': {'$in': demos}, 'at': {'$lt': upper}})
    feedback_rows = await db.feedback.aggregate([{'$match': match}, {'$group': {'_id': None, 'count': {'$sum': 1}, 'average': {'$avg': '$rating'}}}]).to_list(1)
    fb = feedback_rows[0] if feedback_rows else {}
    return EvidenceSummary(start=start, end=end, sample_size=len(actors), demo_starts=len(demos),
        first_replies=counts.get('first_reply', 0), completed_grading=counts.get('grading_completed', 0),
        completion_rate=round(100 * finished / len(demos), 1) if demos else 0,
        returning_users=sum(len(a['days']) > 1 for a in actors), retry_starts=counts.get('retry_started', 0),
        retry_completions=counts.get('retry_completed', 0), comparable_improvements=counts.get('comparable_improvement', 0),
        feedback_count=fb.get('count', 0), feedback_average=round(fb['average'], 2) if fb else None,
        note='Instrumented usage only, from this release onward. Fixture/internal accounts excluded. Sample size means unique practice users, not customers. Return use means practice on distinct UTC days within the range. Demo completion is the start cohort completed by the range end. Comparable improvements refer only to matched targeted retry assessments. No revenue or time-saving claims inferred.')