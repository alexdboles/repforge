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
  speaker: "rep" | "prospect";
  text: string;
  at: number;
}

export interface TurnResponse {
  reply: string;
  turn_index: number;
}

export interface CategoryScore {
  category: string;
  score: number;
  note: string;
}

export interface Strength {
  title: string;
  detail: string;
  quote: string;
}

export interface Miss {
  title: string;
  detail: string;
  quote: string;
  better_approach: string;
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
}

export interface Simulation {
  id: string;
  user_id: string;
  exercise_id: string;
  exercise_name: string;
  difficulty: number;
  difficulty_name: string;
  scenario: ScenarioBrief;
  status: "active" | "completed";
  mode: "guided" | "business";
  voice_persona: string;
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

export interface Nudge {
  level: "fresh" | "due" | "lapsed" | "never";
  days_since: number | null;
  headline: string;
  detail: string;
}

export interface Assignment {
  id: string;
  user_id: string;
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
  assignments: Assignment[];
  completed: number;
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
