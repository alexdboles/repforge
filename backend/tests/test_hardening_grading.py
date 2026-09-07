import asyncio
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from lib.grading import validate_grade, lexical_metrics, rubric_for
from lib.analytics import build_readiness, build_nudge, dated_comparable_trend
from lib.db import db
from routers.users import dashboard

TRANSCRIPT = [{'speaker': 'prospect', 'text': 'Our handovers keep failing.'},
              {'speaker': 'rep', 'text': 'How does that affect your team?'}]


def valid_grade():
    return {'overall_score': 99, 'headline': 'Explore the consequence.',
        'category_scores': [{'category': 'Discovery', 'score': 60, 'note': 'Relevant question, incomplete depth.',
            'evidence': [{'turn_index': 1, 'quote': TRANSCRIPT[1]['text']}]}],
        'strengths': [], 'misses': [{'title': 'Quantify the consequence', 'detail': 'Ask what the delay costs.',
            'quote': TRANSCRIPT[0]['text'], 'turn_index': 0, 'category': 'Discovery', 'better_approach': 'What does one delayed handover cost?'}],
        'coaching_priorities': [{'skill': 'Discovery', 'why': 'No cost established', 'drill': 'Ask about the cost'}],
        'recommended_exercise_id': 'discovery', 'recommended_difficulty': 2, 'recommended_reason': 'Explore impact',
        'metrics': {}, 'moments': [{'tag': 'strong-question', 'turn_index': 1, 'explanation': 'Explores impact'}],
        'objective_met': False, 'objective_note': 'No next step agreed'}


@pytest.mark.parametrize('defect', ['empty', 'false-string', 'score-string', 'missing-category', 'bad-quote', 'bad-reference', 'bad-tag', 'bad-recommendation', 'audio-confidence'])
def test_invalid_assessment_rejected(defect):
    raw = deepcopy(valid_grade())
    if defect == 'empty': raw = {}
    if defect == 'false-string': raw['objective_met'] = 'false'
    if defect == 'score-string': raw['category_scores'][0]['score'] = '100'
    if defect == 'missing-category': raw['category_scores'] = []
    if defect == 'bad-quote': raw['misses'][0]['quote'] = 'Invented quote'
    if defect == 'bad-reference': raw['category_scores'][0]['evidence'][0]['turn_index'] = 55
    if defect == 'bad-tag': raw['moments'][0]['tag'] = 'audio-confidence'
    if defect == 'bad-recommendation': raw['recommended_exercise_id'] = 'perfect-score'
    if defect == 'audio-confidence': raw['category_scores'][0]['category'] = 'Confidence'
    with pytest.raises(ValueError):
        validate_grade(raw, TRANSCRIPT, rubric_for('discovery'), 'controlled-model', 2)


def test_validated_weighted_result_and_zero():
    raw = valid_grade()
    result = validate_grade(raw, TRANSCRIPT, rubric_for('discovery'), 'controlled-model', 2)
    assert result['overall_score'] == 60
    assert result['objective_met'] is False
    raw['category_scores'][0]['score'] = 0
    assert validate_grade(raw, TRANSCRIPT, rubric_for('discovery'), 'controlled-model', 2)['overall_score'] == 0
    assert result['evidence_validated'] and result['transcript_version'] == 2


def test_priority_schema_matches_validator():
    from lib.llm import EVAL_SCHEMA
    assert 'EXACT category string already present in your category_scores' in EVAL_SCHEMA
    raw = valid_grade()
    raw['coaching_priorities'][0]['skill'] = 'Problem-based cold call opener'
    with pytest.raises(ValueError, match='Priority must refer'):
        validate_grade(raw, TRANSCRIPT, rubric_for('discovery'), 'controlled-model', 2)


def test_lexical_counts_and_coverage():
    metrics = lexical_metrics(TRANSCRIPT)
    assert metrics['rep_words'] == 6 and metrics['prospect_words'] == 4
    assert metrics['talk_ratio'] == 60 and metrics['open_questions'] == 1
    readiness = build_readiness([{'category': 'Discovery', 'average': 80, 'attempts': 1}], [{}])
    assert readiness['score'] == 80
    assert all(c['score'] is None for c in readiness['categories'] if not c['attempts'])
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    assert 'yesterday' in build_nudge({'last_practice_date': yesterday}, [{}])['detail']


@pytest.mark.asyncio(loop_scope='session')
async def test_more_than_500_and_order_independent():
    await many_records()


@pytest.mark.asyncio(loop_scope='session')
async def test_one_bounded_repair_without_relaxing_validation():
    from routers.simulations import _validated_evaluation
    from lib.llm import EvalRequest
    req = EvalRequest('internal', {}, {}, {}, TRANSCRIPT, 0)
    with patch('routers.simulations.evaluate_conversation', AsyncMock(side_effect=[{}, valid_grade()])) as provider:
        result = await _validated_evaluation(req, rubric_for('discovery'), 2)
        assert result.evidence_validated and provider.await_count == 2
    with patch('routers.simulations.evaluate_conversation', AsyncMock(return_value={})) as provider:
        with pytest.raises(ValueError):
            await _validated_evaluation(req, rubric_for('discovery'), 2)
        assert provider.await_count == 2


@pytest.mark.asyncio(loop_scope='session')
async def test_full_coached_retry_source_comparison():
    from routers.insights import attempt_series
    uid = 'internal-comparison-' + str(uuid.uuid4())
    base = {'id': uid+'-source', 'user_id': uid, 'exercise_id': 'discovery', 'exercise_name': 'Discovery',
        'difficulty': 2, 'difficulty_name': 'Developing', 'scenario': {'prospect_name': 'Fictional buyer'},
        'status': 'completed', 'mode': 'guided', 'started_at': datetime.now(timezone.utc), 'assisted': False,
        'rubric_snapshot': rubric_for('discovery'), 'evaluation': {'overall_score': 40, 'evidence_validated': True,
        'category_scores': [{'category': 'Discovery', 'score': 40}], 'metrics': {}}}
    retry = {**base, 'id': uid+'-retry', 'assisted': True, 'retry_of': base['id'],
        'evaluation': {**base['evaluation'], 'overall_score': 60, 'category_scores': [{'category': 'Discovery', 'score': 60}]}}
    await db.simulations.insert_many([base, retry])
    try:
        result = await attempt_series(uid, 'discovery', retry['id'], {'id': uid})
        assert len(result.attempts) == 2 and result.comparison_kind == 'coached_source'
        assert result.category_deltas == {'Discovery': 20}
        assert 'not unaided improvement' in result.comparison_note
    finally:
        await db.simulations.delete_many({'user_id': uid})


async def many_records():
    uid = 'internal-550-' + str(uuid.uuid4())
    await db.users.insert_one({'id': uid, 'name': 'Internal report fixture', 'is_internal': True})
    now = datetime.now(timezone.utc)
    docs = [{'id': f'{uid}-{i}', 'user_id': uid, 'exercise_id': 'discovery', 'exercise_name': 'Discovery',
        'difficulty': 2, 'difficulty_name': 'Developing', 'scenario': {'prospect_name': 'Fixture', 'company': 'Fixture'},
        'status': 'completed', 'mode': 'guided', 'started_at': now - timedelta(minutes=550-i), 'duration_seconds': 120,
        'evaluation': {'overall_score': 0 if i == 549 else 60, 'category_scores': [], 'metrics': {}, 'evidence_validated': True}}
        for i in range(550)]
    try:
        await db.simulations.insert_many(docs)
        result = await dashboard(uid, {'id': uid})
        assert result.completed == 550 and result.recent_score == 0
        assert result.recent[0].id == f'{uid}-549'
        assert dated_comparable_trend(docs) == dated_comparable_trend(list(reversed(docs)))
    finally:
        await db.simulations.delete_many({'user_id': uid})
        await db.users.delete_one({'id': uid})