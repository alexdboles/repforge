"""Strict NEW assessment validation; legacy reports remain readable, never regraded silently."""
import re
from pydantic import BaseModel, ConfigDict, Field
from lib.catalog import SKILL_CATEGORIES, exercise_by_id
from lib.curriculum import focus_categories, graded_principles

RUBRIC_VERSION = 'consultative-evidence-v2'
TAGS = {'strong-question', 'missed-discovery', 'objection', 'premature-pitch', 'strong-value', 'buying-signal', 'closing-opportunity'}


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')


class Evidence(StrictModel):
    turn_index: int = Field(ge=0)
    quote: str = Field(min_length=1, max_length=2000)


class AssessedCategory(StrictModel):
    category: str
    score: int = Field(ge=0, le=100)
    note: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class AssessedStrength(StrictModel):
    title: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    turn_index: int = Field(ge=0)


class AssessedMiss(AssessedStrength):
    better_approach: str = Field(min_length=1)
    category: str


class AssessedPriority(StrictModel):
    skill: str
    why: str = Field(min_length=1)
    drill: str = Field(min_length=1)


class AssessedMoment(StrictModel):
    tag: str
    turn_index: int = Field(ge=0)
    explanation: str = Field(min_length=1)


class GradeDraft(StrictModel):
    overall_score: int = Field(ge=0, le=100)
    headline: str = Field(min_length=1)
    category_scores: list[AssessedCategory] = Field(min_length=1, max_length=15)
    strengths: list[AssessedStrength]
    misses: list[AssessedMiss]
    coaching_priorities: list[AssessedPriority] = Field(min_length=1, max_length=3)
    recommended_exercise_id: str
    recommended_difficulty: int = Field(ge=1, le=5)
    recommended_reason: str = Field(min_length=1)
    metrics: dict = {}
    moments: list[AssessedMoment]
    objective_met: bool
    objective_note: str = Field(min_length=1)


def rubric_for(exercise_id: str, target: str = '') -> dict:
    focus = focus_categories(exercise_id)
    allowed = [s for s in SKILL_CATEGORIES if s not in ('Confidence', 'Tonality', 'Pacing')]
    return {'version': RUBRIC_VERSION, 'exercise_id': exercise_id,
        'weights': {s: (1 if target else 2 if s in focus else 1) for s in allowed if not target or s == target},
        'criteria': graded_principles(exercise_id),
        'anchors': {'0-24': 'Clear counterproductive behaviour', '25-49': 'Missed or weak response to an evidenced opportunity',
                    '50-74': 'Relevant but incomplete behaviour', '75-89': 'Effective, specific behaviour', '90-100': 'Consistently excellent behaviour in available evidence'},
        'unassessed_rule': 'Omit categories with no opportunity/evidence; never treat missing as zero'}


def lexical_metrics(transcript: list[dict]) -> dict:
    reps = [t['text'] for t in transcript if t['speaker'] == 'rep']
    prospects = [t['text'] for t in transcript if t['speaker'] == 'prospect']
    words = lambda s: re.findall(r"\b[\w]+(?:['’][\w]+)?\b", s, re.UNICODE)
    counts = [len(words(t)) for t in reps]
    rep_words, buyer_words = sum(counts), sum(len(words(t)) for t in prospects)
    # Explicit lexical heuristic, not inferred acoustic behaviour.
    questions = [part.strip() for t in reps for part in re.findall(r'([^.!?]*\?)', t)]
    opens = sum(bool(re.match(r'^(what|how|why|tell me|describe)\b', q, re.I)) for q in questions)
    return {'talk_ratio': round(100 * rep_words / max(1, rep_words + buyer_words)), 'rep_words': rep_words,
        'prospect_words': buyer_words, 'question_count': len(questions), 'open_questions': opens,
        'closed_questions': len(questions) - opens,
        'filler_words': len(re.findall(r'\b(?:um|uh|erm|you know)\b', ' '.join(reps), re.I)),
        'avg_response_words': round(rep_words / max(1, len(reps))), 'longest_monologue_words': max(counts, default=0),
        'objection_count': 0, 'objections_handled': 0}


def validate_grade(raw: dict, transcript: list[dict], rubric: dict, model: str, transcript_version: int) -> dict:
    draft = GradeDraft.model_validate(raw)
    allowed = rubric['weights']
    seen = set()
    def evidence(index, quote=None):
        if index >= len(transcript):
            raise ValueError('Evidence turn does not exist')
        if quote is not None and quote not in transcript[index]['text']:
            raise ValueError('Exact quotation does not match frozen transcript')
    for category in draft.category_scores:
        if category.category not in allowed or category.category in seen:
            raise ValueError('Unsupported or duplicate category')
        seen.add(category.category)
        for item in category.evidence:
            evidence(item.turn_index, item.quote)
    for item in [*draft.strengths, *draft.misses]:
        evidence(item.turn_index, item.quote)
    for miss in draft.misses:
        if miss.category not in seen:
            raise ValueError('Retry objective must refer to an assessed category')
    for priority in draft.coaching_priorities:
        if priority.skill not in seen:
            raise ValueError('Priority must refer to an assessed category')
    for moment in draft.moments:
        if moment.tag not in TAGS:
            raise ValueError('Unsupported moment tag')
        evidence(moment.turn_index)
    if not exercise_by_id(draft.recommended_exercise_id):
        raise ValueError('Unknown recommended exercise')
    out = draft.model_dump()
    total_weight = sum(allowed[c.category] for c in draft.category_scores)
    out['overall_score'] = round(sum(c.score * allowed[c.category] for c in draft.category_scores) / total_weight)
    out['metrics'] = lexical_metrics(transcript)
    out['metrics']['objection_count'] = sum(m.tag == 'objection' for m in draft.moments)
    # Objection effectiveness is not a measured count; leave it explicitly unassessed.
    out['unassessed_categories'] = [c for c in allowed if c not in seen]
    out['rubric_version'] = rubric['version']
    out['rubric_weights'] = allowed
    out['model_version'] = model
    out['transcript_version'] = transcript_version
    out['evidence_validated'] = True
    return out