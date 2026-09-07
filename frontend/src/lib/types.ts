// Hand-written mirrors of backend/models/schemas.py — keep in sync in the same edit.

export interface Exercise {
  id: string;
  name: string;
  tagline: string;
  description: string;
  skills: string[];
  duration_min: number;
  icon: string;
}

export interface Difficulty {
  level: number;
  name: string;
  subtitle: string;
  behavior: string;
  unlock_xp: number;
}

export interface ProductSheet {
  name: string;
  one_liner: string;
  features: string[];
  benefits: string[];
  pricing: string;
  differentiators: string[];
  limitations: string[];
  use_cases: string[];
}

export interface ScenarioBrief {
  id: string;
  product: string;
  seller_role: string;
  product_sheet: ProductSheet | null;
  things_to_remember: string[];
  prospect_name: string;
  prospect_role: string;
  company: string;
  company_size: string;
  industry: string;
  known: string;
  objective: string;
  mood: string;
  objections: string[];
  hidden?: string;
  personality?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  role: string;
  experience_level: string;
  org: string;
  workspace_id: string;
  workspace_role: string;
  is_guest: boolean;
  is_admin: boolean;
  xp: number;
  level: number;
  streak: number;
  last_practice_date: string | null;
  badges: string[];
  trained_skills: string[];
  created_at: string;
}

export interface Term {
  term: string;
  definition: string;
}

export interface FrameworkStep {
  label: string;
  detail: string;
}

export interface ExamplePair {
  weak: string;
  strong: string;
  why: string;
}

export interface QuizItem {
  question: string;
  options: string[];
  answer: number;
  explanation: string;
}

export interface TrainingModule {
  exercise_id: string;
  title: string;
  promise: string;
  duration_min: number;
  objectives: string[];
  why_it_matters: string;
  when_used: string;
  terms: Term[];
  framework: { name: string; steps: FrameworkStep[] };
  examples: ExamplePair[];
  mistakes: string[];
  strong_performance: string[];
  knowledge_check: QuizItem[];
  focus_categories: string[];
  graded_principles: string[];
}

export interface SalesProfileInput {
  label: string;
  company: string;
  industry: string;
  product: string;
  product_description: string;
  problems_solved: string;
  benefits: string;
  differentiators: string;
  customer_type: string;
  customer_industries: string;
  customer_titles: string;
  ideal_customer: string;
  call_goal: string;
  sales_cycle: string;
  pricing: string;
  competitors: string;
  competitor_advantages: string;
  our_advantages: string;
  common_objections: string[];
  methodology: string;
  extra_context: string;
}

export interface SalesProfile extends SalesProfileInput {
  id: string;
  user_id: string;
  created_at: string;
}

export interface CustomScenario {
  id: string;
  user_id: string;
  profile_id: string;
  exercise_id: string;
  difficulty: number;
  product: string;
  seller_role: string;
  prospect_name: string;
  prospect_role: string;
  company: string;
  company_size: string;
  industry: string;
  known: string;
  objective: string;
  mood: string;
  personality: string;
  objections: string[];
  created_at: string;
}

export interface VoiceStatus {
  provider: string;
  available: boolean;
  message: string;
  voices: string[];
}

export interface TranscriptTurn {
  id?: string;
  request_key?: string;
  speaker: "rep" | "prospect";
  text: string;
  at: number;
}

export interface TurnResponse {
  reply: string;
  turn_index: number;
  version: number;
  transcript: TranscriptTurn[];
}

export interface CategoryScore {
  category: string;
  score: number;
  note: string;
  evidence?: Evidence[];
}

export interface Strength {
  title: string;
  detail: string;
  quote: string;
  turn_index?: number | null;
}

export interface Miss {
  title: string;
  detail: string;
  quote: string;
  better_approach: string;
  turn_index?: number | null;
  category?: string;
}

export interface CoachingPriority {
  skill: string;
  why: string;
  drill: string;
}

export interface Metrics {
  talk_ratio: number;
  question_count: number;
  open_questions: number;
  closed_questions: number;
  filler_words: number;
  avg_response_words: number;
  longest_monologue_words: number;
  objection_count: number;
  objections_handled: number;
  rep_words?: number;
  prospect_words?: number;
}

export interface Moment {
  tag: string;
  turn_index: number;
  explanation: string;
}

export interface Evaluation {
  overall_score: number;
  headline: string;
  category_scores: CategoryScore[];
  strengths: Strength[];
  misses: Miss[];
  coaching_priorities: CoachingPriority[];
  recommended_exercise_id: string;
  recommended_difficulty: number;
  recommended_reason: string;
  metrics: Metrics;
  moments: Moment[];
  objective_met: boolean;
  objective_note: string;
  unassessed_categories?: string[];
  rubric_version?: string;
  rubric_weights?: Record<string, number>;
  model_version?: string;
  transcript_version?: number;
  evidence_validated?: boolean;
}

export interface Simulation {
  id: string;
  user_id: string;
  exercise_id: string;
  exercise_name: string;
  difficulty: number;
  difficulty_name: string;
  scenario: ScenarioBrief;
  status: 'preparation' | 'active' | 'ending' | 'grading' | 'grading_failed' | 'analyzing' | 'completed' | 'abandoned';
  version: number;
  frozen_version: number | null;
  call_started_at: string | null;
  assignment_id: string | null;
  assisted: boolean;
  is_demo: boolean;
  voice_config: Record<string, unknown>;
  rubric_version: string;
  grading_error: string;
  rubric_snapshot: Record<string, unknown>;
  moment_category: string;
  moment_baseline: number | null;
  moment_score: number | null;
  source_turn_index: number | null;
  mode: "guided" | "business" | "journey" | "moment";
  // Retry That Moment (mirrors backend Simulation)
  retry_of: string | null;
  moment_label: string;
  moment_situation: string;
  moment_objective: string;
  origin_score: number;
  moment_improved: boolean | null;
  voice_persona: string;
  journey_id: string | null;
  prior_context: string;
  transcript: TranscriptTurn[];
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  evaluation: Evaluation | null;
  xp_awarded: number;
}

export interface SimulationSummary {
  id: string;
  exercise_id: string;
  exercise_name: string;
  difficulty: number;
  difficulty_name: string;
  prospect_name: string;
  company: string;
  status: string;
  started_at: string;
  duration_seconds: number;
  overall_score: number | null;
  turns: number;
}

export interface SkillStat {
  category: string;
  average: number;
  attempts: number;
  trend: number;
}

export interface TrendPoint {
  index: number;
  label: string;
  score: number;
  exercise_name: string;
}

export interface ExerciseStat {
  exercise_id: string;
  exercise_name: string;
  attempts: number;
  average: number;
  best: number;
}

export interface Recommendation {
  exercise_id: string;
  exercise_name: string;
  difficulty: number;
  difficulty_name: string;
  reason: string;
}

export interface BadgeItem {
  id: string;
  name: string;
  description: string;
  earned: boolean;
}

export interface Hint {
  stage: string;
  goal: string;
  example: string;
  avoid: string;
  reveal_example: boolean;
}

export interface LearningStage {
  id: string;
  order: number;
  name: string;
  goal: string;
  exercise_ids: string[];
}

export interface JourneyStage {
  exercise_id: string;
  objective: string;
  situation: string;
  mood: string;
  completed: boolean;
  best_score: number | null;
  simulation_id: string | null;
}

export interface JourneyView {
  id: string;
  title: string;
  blurb: string;
  character: string;
  role: string;
  company: string;
  company_size: string;
  industry: string;
  product: string;
  seller_role: string;
  public: string;
  stages: JourneyStage[];
  completed_stages: number;
  next_exercise_id: string | null;
}

export interface ReadinessCategory {
  category: string;
  score: number | null;
  weight: number;
  attempts: number;
}

export interface Readiness {
  score: number;
  label: string;
  categories: ReadinessCategory[];
  biggest_opportunity: string | null;
  recommendation: string;
  covered: number;
  total_weighted: number;
}

export interface Nudge {
  level: "fresh" | "due" | "lapsed" | "never";
  days_since: number | null;
  headline: string;
  detail: string;
}

export interface Assignment {
  id: string;
  user_id: string;
  workspace_id: string;
  membership_unverified: boolean;
  user_name: string;
  org: string;
  exercise_id: string;
  exercise_name: string;
  difficulty: number;
  difficulty_name: string;
  note: string;
  assigned_by: string;
  status: "pending" | "completed";
  created_at: string;
  completed_at: string | null;
  completed_simulation_id: string | null;
  score: number | null;
}

export interface Dashboard {
  user: UserProfile;
  nudge: Nudge;
  readiness: Readiness;
  assignments: Assignment[];
  completed: number;
  full_calls: number;
  moment_drills: number;
  assisted_calls: number;
  assessed_calls: number;
  average_score: number;
  recent_score: number | null;
  improvement: number;
  personal_best: number | null;
  strongest_skill: SkillStat | null;
  weakest_skill: SkillStat | null;
  trend: TrendPoint[];
  skills: SkillStat[];
  exercise_stats: ExerciseStat[];
  difficulty_reached: number;
  unlocked_difficulty: number;
  recommendation: Recommendation;
  recent: SimulationSummary[];
  total_practice_seconds: number;
  badges: BadgeItem[];
}

export interface Attempt {
  index: number;
  simulation_id: string;
  started_at: string;
  difficulty: number;
  difficulty_name: string;
  mode: string;
  prospect_name: string;
  overall_score: number;
  categories: Record<string, number>;
  talk_ratio: number;
  question_count: number;
}

export interface AttemptSeries {
  exercise_id: string;
  exercise_name: string;
  attempts: Attempt[];
  first_score: number | null;
  latest_score: number | null;
  best_score: number | null;
  delta: number;
  category_deltas: Record<string, number>;
  most_improved: string | null;
  still_weakest: string | null;
  comparison_kind: 'matched_assessment' | 'coached_source';
  comparison_note: string;
}

export interface TeamMember {
  user_id: string;
  name: string;
  experience_level: string;
  reps: number;
  average_score: number | null;
  latest_score: number | null;
  improvement: number;
  practice_seconds: number;
  last_practice_date: string | null;
  weakest_skill: string | null;
  level: number;
  xp: number;
}

export interface TeamView {
  org: string;
  assignments: Assignment[];
  lapsed_members: string[];
  members: TeamMember[];
  total_reps: number;
  total_practice_seconds: number;
  team_average: number | null;
  team_improvement: number;
  skill_gaps: SkillStat[];
  exercise_coverage: ExerciseStat[];
  leaderboard: TeamMember[];
  manager_hours_saved: number;
}

// Mirrors backend/routers/voice.py :: CastVoice
export interface CastVoice {
  character: string;
  role: string;
  voice_label: string;
  style_note: string;
  stability: number;
  similarity_boost: number;
  speed: number;
  verified: boolean;
  detail: string;
}

// Mirrors backend/models/schemas.py :: SessionResponse
export interface SessionResponse {
  user: UserProfile;
  token: string;
}

export interface InvitationCreate { email: string; role: "member" | "manager" }
export interface InvitationResponse { token: string; expires_at: string }
export interface InvitationAccept { token: string }
export interface Health { status: "ok" }
export interface SpeakRequest { simulation_id: string; turn_id?: string; text?: string; character?: string; persona?: string; difficulty?: number }
export interface SampleRequest { simulation_id: string }
export interface QASampleRequest { character: string; line?: number }
export interface FeedbackRequest { simulation_id: string; rating: number }
export interface FeedbackResponse { saved: boolean }
export interface EvidenceSummary { start: string; end: string; sample_size: number; demo_starts: number; first_replies: number; completed_grading: number; completion_rate: number; returning_users: number; retry_starts: number; retry_completions: number; comparable_improvements: number; feedback_count: number; feedback_average: number | null; note: string }
export interface TurnRequest { text: string; at?: number; idempotency_key?: string; expected_version?: number }
export interface SimulationStart { user_id: string; exercise_id: string; difficulty: number; scenario_id?: string; custom_scenario_id?: string; journey_id?: string; mode?: 'guided' | 'business' | 'journey' | 'moment'; assignment_id?: string; is_demo?: boolean }
export interface Evidence { turn_index: number; quote: string }
export interface AssessedCategory { category: string; score: number; note: string; evidence: Evidence[] }
export interface AssessedStrength { title: string; detail: string; quote: string; turn_index: number }
export interface AssessedMiss extends AssessedStrength { better_approach: string; category: string }
export interface AssessedPriority { skill: string; why: string; drill: string }
export interface AssessedMoment { tag: string; turn_index: number; explanation: string }
export interface GradeDraft { overall_score: number; headline: string; category_scores: AssessedCategory[]; strengths: AssessedStrength[]; misses: AssessedMiss[]; coaching_priorities: AssessedPriority[]; recommended_exercise_id: string; recommended_difficulty: number; recommended_reason: string; metrics: Record<string, unknown>; moments: AssessedMoment[]; objective_met: boolean; objective_note: string }
