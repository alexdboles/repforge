"""Pydantic v2 models. Each has a hand-written TS mirror in frontend/src/lib/types.ts."""
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
import uuid


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


# ---------- catalog ----------
class Exercise(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    skills: list[str]
    duration_min: int
    icon: str


class Difficulty(BaseModel):
    level: int
    name: str
    subtitle: str
    behavior: str
    unlock_xp: int


class ProductSheet(BaseModel):
    name: str
    one_liner: str
    features: list[str] = []
    benefits: list[str] = []
    pricing: str = ""
    differentiators: list[str] = []
    limitations: list[str] = []
    use_cases: list[str] = []


class ScenarioBrief(BaseModel):
    id: str
    product: str
    seller_role: str = ""
    product_sheet: Optional[ProductSheet] = None
    things_to_remember: list[str] = []
    prospect_name: str
    prospect_role: str
    company: str
    company_size: str
    industry: str
    known: str
    objective: str
    mood: str
    objections: list[str]


# ---------- curriculum ----------
class Term(BaseModel):
    term: str
    definition: str


class FrameworkStep(BaseModel):
    label: str
    detail: str


class Framework(BaseModel):
    name: str
    steps: list[FrameworkStep]


class ExamplePair(BaseModel):
    weak: str
    strong: str
    why: str


class QuizItem(BaseModel):
    question: str
    options: list[str]
    answer: int
    explanation: str


class TrainingModule(BaseModel):
    exercise_id: str
    title: str
    promise: str
    duration_min: int
    objectives: list[str]
    why_it_matters: str
    when_used: str
    terms: list[Term]
    framework: Framework
    examples: list[ExamplePair]
    mistakes: list[str]
    strong_performance: list[str]
    knowledge_check: list[QuizItem]
    focus_categories: list[str]
    graded_principles: list[str]


# ---------- sales profiles (Practice My Business) ----------
class SalesProfileInput(BaseModel):
    label: str
    company: str
    industry: str = ""
    product: str
    product_description: str = ""
    problems_solved: str = ""
    benefits: str = ""
    differentiators: str = ""
    customer_type: str = "Small businesses"
    customer_industries: str = ""
    customer_titles: str = ""
    ideal_customer: str = ""
    call_goal: str = "Book a meeting"
    sales_cycle: str = ""
    pricing: str = ""
    competitors: str = ""
    competitor_advantages: str = ""
    our_advantages: str = ""
    common_objections: list[str] = []
    methodology: str = "No formal methodology"
    extra_context: str = ""


class SalesProfile(SalesProfileInput):
    id: str = Field(default_factory=_uid)
    user_id: str
    created_at: datetime = Field(default_factory=_now)


class CustomScenarioRequest(BaseModel):
    profile_id: str
    exercise_id: str
    difficulty: int
    preferences: str = ""


class CustomScenario(BaseModel):
    id: str = Field(default_factory=_uid)
    user_id: str
    profile_id: str
    exercise_id: str
    difficulty: int
    product: str
    seller_role: str
    prospect_name: str
    prospect_role: str
    company: str
    company_size: str
    industry: str
    known: str
    objective: str
    mood: str
    personality: str
    objections: list[str] = []
    created_at: datetime = Field(default_factory=_now)


# ---------- voice ----------
class VoiceStatus(BaseModel):
    provider: str
    available: bool
    message: str
    voices: list[str] = []


# ---------- users ----------
class UserProfile(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str
    role: str = "Sales Professional"
    experience_level: str = "New"
    org: str = "Personal"
    xp: int = 0
    level: int = 1
    streak: int = 0
    last_practice_date: Optional[str] = None
    badges: list[str] = []
    trained_skills: list[str] = []
    created_at: datetime = Field(default_factory=_now)


class UserCreate(BaseModel):
    name: str
    experience_level: str = "New"
    role: str = "Sales Professional"
    org: str = "Personal"


# ---------- simulations ----------
class TranscriptTurn(BaseModel):
    speaker: Literal["rep", "prospect"]
    text: str
    at: float = 0.0


class SimulationStart(BaseModel):
    user_id: str
    exercise_id: str
    difficulty: int
    scenario_id: Optional[str] = None
    custom_scenario_id: Optional[str] = None
    mode: Literal["guided", "business"] = "guided"


class TurnRequest(BaseModel):
    text: str
    at: float = 0.0


class TurnResponse(BaseModel):
    reply: str
    turn_index: int


class CategoryScore(BaseModel):
    category: str = "General"
    score: int = 0
    note: str = ""


class Strength(BaseModel):
    title: str = "Strength"
    detail: str = ""
    quote: str = ""


class Miss(BaseModel):
    title: str = "Missed opportunity"
    detail: str = ""
    quote: str = ""
    better_approach: str = ""


class CoachingPriority(BaseModel):
    skill: str = "Discovery"
    why: str = ""
    drill: str = ""


class Metrics(BaseModel):
    talk_ratio: int = 0
    question_count: int = 0
    open_questions: int = 0
    closed_questions: int = 0
    filler_words: int = 0
    avg_response_words: int = 0
    longest_monologue_words: int = 0
    objection_count: int = 0
    objections_handled: int = 0


class Moment(BaseModel):
    tag: str = "strong-question"
    turn_index: int = 0
    explanation: str = ""


class Evaluation(BaseModel):
    overall_score: int = 0
    headline: str = ""
    category_scores: list[CategoryScore] = []
    strengths: list[Strength] = []
    misses: list[Miss] = []
    coaching_priorities: list[CoachingPriority] = []
    recommended_exercise_id: str = "discovery"
    recommended_difficulty: int = 2
    recommended_reason: str = ""
    metrics: Metrics = Metrics()
    moments: list[Moment] = []
    objective_met: bool = False
    objective_note: str = ""


class Simulation(BaseModel):
    id: str = Field(default_factory=_uid)
    user_id: str
    exercise_id: str
    exercise_name: str
    difficulty: int
    difficulty_name: str
    scenario: dict[str, Any]
    status: Literal["active", "completed"] = "active"
    mode: Literal["guided", "business"] = "guided"
    voice_persona: str = "default"
    transcript: list[TranscriptTurn] = []
    started_at: datetime = Field(default_factory=_now)
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    evaluation: Optional[Evaluation] = None
    xp_awarded: int = 0


class SimulationSummary(BaseModel):
    id: str
    exercise_id: str
    exercise_name: str
    difficulty: int
    difficulty_name: str
    prospect_name: str
    company: str
    status: str
    started_at: datetime
    duration_seconds: int
    overall_score: Optional[int] = None
    turns: int = 0


# ---------- attempt comparison ----------
class Attempt(BaseModel):
    index: int
    simulation_id: str
    started_at: datetime
    difficulty: int
    difficulty_name: str
    mode: str
    prospect_name: str
    overall_score: int
    categories: dict[str, int] = {}
    talk_ratio: int = 0
    question_count: int = 0


class AttemptSeries(BaseModel):
    exercise_id: str
    exercise_name: str
    attempts: list[Attempt] = []
    first_score: Optional[int] = None
    latest_score: Optional[int] = None
    best_score: Optional[int] = None
    delta: int = 0
    category_deltas: dict[str, int] = {}
    most_improved: Optional[str] = None
    still_weakest: Optional[str] = None


# ---------- dashboard / progress ----------
class SkillStat(BaseModel):
    category: str
    average: int
    attempts: int
    trend: int


class TrendPoint(BaseModel):
    index: int
    label: str
    score: int
    exercise_name: str


class ExerciseStat(BaseModel):
    exercise_id: str
    exercise_name: str
    attempts: int
    average: int
    best: int


# ---------- assigned training ----------
class AssignmentCreate(BaseModel):
    user_id: str
    exercise_id: str
    difficulty: int = 2
    note: str = ""
    assigned_by: str = "Manager"
    org: str = ""


class Assignment(BaseModel):
    id: str = Field(default_factory=_uid)
    user_id: str
    user_name: str = ""
    org: str = ""
    exercise_id: str
    exercise_name: str = ""
    difficulty: int = 2
    difficulty_name: str = ""
    note: str = ""
    assigned_by: str = "Manager"
    status: Literal["pending", "completed"] = "pending"
    created_at: datetime = Field(default_factory=_now)
    completed_at: Optional[datetime] = None
    completed_simulation_id: Optional[str] = None
    score: Optional[int] = None


# ---------- practice nudge ----------
class Nudge(BaseModel):
    level: Literal["fresh", "due", "lapsed", "never"] = "never"
    days_since: Optional[int] = None
    headline: str
    detail: str


# ---------- team / manager view ----------
class TeamMember(BaseModel):
    user_id: str
    name: str
    experience_level: str
    reps: int
    average_score: Optional[int] = None
    latest_score: Optional[int] = None
    improvement: int = 0
    practice_seconds: int = 0
    last_practice_date: Optional[str] = None
    weakest_skill: Optional[str] = None
    level: int = 1
    xp: int = 0


class TeamView(BaseModel):
    org: str
    assignments: list[Assignment] = []
    lapsed_members: list[str] = []
    members: list[TeamMember] = []
    total_reps: int = 0
    total_practice_seconds: int = 0
    team_average: Optional[int] = None
    team_improvement: int = 0
    skill_gaps: list[SkillStat] = []
    exercise_coverage: list[ExerciseStat] = []
    leaderboard: list[TeamMember] = []
    manager_hours_saved: float = 0.0


class Recommendation(BaseModel):
    exercise_id: str
    exercise_name: str
    difficulty: int
    difficulty_name: str
    reason: str


class Dashboard(BaseModel):
    user: UserProfile
    nudge: Nudge
    assignments: list[Assignment] = []
    completed: int
    average_score: int
    recent_score: Optional[int] = None
    improvement: int = 0
    personal_best: Optional[int] = None
    strongest_skill: Optional[SkillStat] = None
    weakest_skill: Optional[SkillStat] = None
    trend: list[TrendPoint] = []
    skills: list[SkillStat] = []
    exercise_stats: list[ExerciseStat] = []
    difficulty_reached: int = 1
    unlocked_difficulty: int = 2
    recommendation: Recommendation
    recent: list[SimulationSummary] = []
    total_practice_seconds: int = 0
    badges: list[dict[str, Any]] = []
