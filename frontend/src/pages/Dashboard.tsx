import { Link, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  ArrowUpRight,
  BellRing,
  Briefcase,
  ClipboardCheck,
  Flame,
  GraduationCap,
  TrendingDown,
  TrendingUp,
  Loader2,
  Zap,
} from "lucide-react";
import { apiGet } from "@/lib/api";
import { useDemoLaunch } from '@/lib/demo';
import { getUserId, formatDuration, scoreTone } from "@/lib/profile";
import type { Dashboard as DashboardData, Readiness } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { DifficultyPips, EmptyState, ScoreRing, SkillBar, StatCard } from "@/components/Metrics";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export default function Dashboard() {
  const userId = getUserId();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => apiGet<DashboardData>(`/users/${userId}/dashboard`),
    enabled: Boolean(userId),
    retry: false,
  });

  if (!userId) return <Navigate to="/" replace />;

  const d = data;
  const hasData = Boolean(d && d.completed > 0);

  return (
    <AppShell>
      <div className='flex flex-col' data-testid="dashboard-page">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              {d ? `Welcome back, ${d.user.name.split(" ")[0]}.` : "Your performance"}
            </h1>
            <p className="mt-1.5 text-[14px] text-muted-foreground">
              Practice the conversation before it counts — how am I performing, what's improving, what's next.
            </p>
          </div>
          <Link
            to="/training"
            data-testid="dashboard-start-simulation"
            className={cn(buttonVariants({ size: "lg" }), "font-semibold")}
          >
            {hasData ? "Start a simulation" : "Start Your First Simulation"}
            <ArrowRight className="size-4" />
          </Link>
        </div>

        <div className={hasData ? 'order-10' : ''}><DemoLaunch /></div>
        {hasData && d ? <section className='mt-6 rounded-xl border border-blue-200 bg-blue-50 p-5' data-testid='dashboard-next-action'><span className='text-xs font-semibold uppercase tracking-wider text-blue-800'>Your next useful rep</span><h2 className='mt-2 font-heading text-xl font-bold'>{d.recommendation.exercise_name}</h2><p className='mt-2 text-sm text-slate-700'>{d.recommendation.reason}</p><Link className={cn(buttonVariants(), 'mt-4')} data-testid='dashboard-next-action-start' to={`/learn/${d.recommendation.exercise_id}?difficulty=${d.recommendation.difficulty}`}>Practise this next</Link><p className='mt-3 text-xs text-slate-600' data-testid='dashboard-session-types'>{d.full_calls} full calls · {d.moment_drills} moment drills · {d.assisted_calls} assisted full calls · {d.assessed_calls} unaided evidence-validated calls</p></section> : null}

        <Link
          to="/sample-report"
          data-testid="sample-report-card"
          className={cn('mt-4 flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card p-5 transition-colors hover:border-slate-300', hasData && 'order-11')}
        >
          <div className="min-w-0 flex-1">
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              See RepForge in action · sample data
            </span>
            <h2 className="mt-1.5 font-heading text-[18px] font-extrabold">
              Sample coaching report
            </h2>
            <p className="mt-1 max-w-xl text-[13.5px] text-muted-foreground">
              See how RepForge breaks down a fictional example, identifies coaching moments and
              turns mistakes into targeted practice.
            </p>
          </div>
          <span className="flex items-center gap-1.5 text-[13.5px] font-semibold text-primary">
            Explore sample report
            <ArrowRight className="size-4" />
          </span>
        </Link>

        {hasData && d?.nudge ? (
          <div
            className={cn(
              "mt-6 flex flex-wrap items-center gap-4 rounded-lg border p-4",
              d.nudge.level === "lapsed"
                ? "border-amber-300 bg-amber-50"
                : d.nudge.level === "due"
                  ? "border-sky-200 bg-sky-50"
                  : "border-emerald-200 bg-emerald-50",
            )}
            data-testid="streak-nudge"
          >
            {d.nudge.level === "fresh" ? (
              <Flame className="size-5 shrink-0 text-orange-600" />
            ) : (
              <BellRing className="size-5 shrink-0 text-amber-700" />
            )}
            <div className="min-w-0 flex-1">
              <div className="font-heading text-[15px] font-bold" data-testid="nudge-headline">
                {d.nudge.headline}
              </div>
              <p className="text-[13px] text-slate-700">{d.nudge.detail}</p>
            </div>
            <Link
              to={`/learn/${d.recommendation.exercise_id}?difficulty=${d.recommendation.difficulty}`}
              className={cn(buttonVariants({ size: "sm" }), "font-semibold")}
              data-testid="nudge-cta"
            >
              Practise now
            </Link>
          </div>
        ) : null}

        {d?.readiness && d.readiness.covered > 0 ? <details className='mt-5' data-testid='readiness-details'><summary className='cursor-pointer text-sm font-semibold' data-testid='readiness-details-toggle'>View assessed skills & coverage</summary><ReadinessCard r={d.readiness} /></details> : null}

        {d?.assignments?.length ? (
          <section className="mt-6 rounded-xl border border-border bg-card p-5" data-testid="assigned-training">
            <div className="flex items-center gap-2">
              <ClipboardCheck className="size-4 text-primary" />
              <h2 className="font-heading text-[17px] font-bold">Assigned to you</h2>
            </div>
            <div className="mt-3 space-y-2">
              {d.assignments.map((a) => (
                <div
                  key={a.id}
                  className={cn(
                    "flex flex-wrap items-center gap-3 rounded-lg border p-3.5",
                    a.status === "completed" ? "border-border bg-secondary/50" : "border-primary/40 bg-accent",
                  )}
                  data-testid={`assignment-${a.id}`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-[14px] font-semibold">
                      {a.exercise_name} · Level {a.difficulty} {a.difficulty_name}
                    </div>
                    <div className="text-[12.5px] text-muted-foreground">
                      From {a.assigned_by}
                      {a.note ? ` — ${a.note}` : ""}
                    </div>
                  </div>
                  {a.membership_unverified ? <span className='text-xs text-amber-800' data-testid={`assignment-unverified-${a.id}`}>Historical assignment — manager verification needed</span> : a.status === "completed" ? (
                    <Link
                      to={`/scorecard/${a.completed_simulation_id}`}
                      className="flex items-center gap-1.5 text-[13px] font-semibold text-emerald-700"
                      data-testid={`assignment-done-${a.id}`}
                    >
                      Completed · {a.score}
                    </Link>
                  ) : (
                    <Link
                      to={`/learn/${a.exercise_id}?difficulty=${a.difficulty}&assignment=${a.id}`}
                      className={cn(buttonVariants({ size: "sm" }), "font-semibold")}
                      data-testid={`assignment-start-${a.id}`}
                    >
                      Start
                      <ArrowRight className="size-3.5" />
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <div className="mt-6 grid gap-4 md:grid-cols-2" data-testid="dashboard-paths">
          <Link
            to="/training"
            data-testid="path-guided-training"
            className="group rounded-xl border border-border bg-card p-5 transition-shadow hover:shadow-sm"
          >
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <GraduationCap className="size-3.5" />
              Guided training
            </div>
            <div className="mt-2 font-heading text-[19px] font-extrabold">
              Learn the skill, then practise it
            </div>
            <p className="mt-1.5 text-[13.5px] leading-relaxed text-muted-foreground">
              Teaching, framework, weak-vs-strong examples and a fictional company with a full
              product sheet — then a live call graded on exactly what you were taught.
            </p>
            <span className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-semibold text-primary">
              Open the training library
              <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>

          <Link
            to="/practice-business"
            data-testid="path-practice-business"
            className="group rounded-xl border border-border bg-[#0F172A] p-5 text-slate-100 transition-shadow hover:shadow-sm"
          >
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              <Briefcase className="size-3.5" />
              Practice my business
            </div>
            <div className="mt-2 font-heading text-[19px] font-extrabold">
              Rehearse your real sales job
            </div>
            <p className="mt-1.5 text-[13.5px] leading-relaxed text-slate-300">
              Save your company, product, pricing, competitors and real objections once. We generate
              a new prospect from it whenever you have a hard call coming up.
            </p>
            <span className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-semibold text-sky-300">
              Set up or launch a custom call
              <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>
        </div>

        {isError ? (
          <div
            className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-[13.5px] text-amber-900"
            data-testid="dashboard-error"
          >
            Live performance data is unavailable right now. Your training library is still available.
            <Button className='ml-3' variant='outline' data-testid='dashboard-retry-data' onClick={() => void refetch()}>Retry</Button>
          </div>
        ) : null}

        {isLoading ? (
          <div className="mt-8 grid gap-4 lg:grid-cols-4" data-testid="dashboard-loading">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-secondary" />
            ))}
          </div>
        ) : null}

        {d && hasData && !isError ? (
          <>
            <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                testid="stat-completed"
                label="Simulations"
                value={String(d.completed)}
                hint={`${formatDuration(d.total_practice_seconds)} of live practice`}
              />
              <StatCard
                testid="stat-average"
                label="Full-call average"
                value={d.completed ? `${d.average_score}` : "—"}
                hint={d.personal_best !== null ? `Personal best ${d.personal_best}` : "No scores yet"}
                tone={d.completed ? scoreTone(d.average_score) : undefined}
              />
              <StatCard
                testid="stat-recent"
                label="Most recent"
                value={d.recent_score !== null ? `${d.recent_score}` : "—"}
                hint={d.recent[0] ? d.recent[0].exercise_name : "Run your first call"}
                tone={d.recent_score !== null ? scoreTone(d.recent_score) : undefined}
              />
              <StatCard
                testid="stat-improvement"
                label="Comparable change"
                value={d.completed >= 2 ? `${d.improvement > 0 ? "+" : ""}${d.improvement}` : "—"}
                hint={
                  d.completed >= 2
                    ? "Same scenario, rubric, difficulty and assistance only"
                    : "Needs comparable assessments"
                }
                tone={d.improvement >= 0 ? "text-emerald-600" : "text-red-600"}
              />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <section className="rounded-lg border border-border bg-card p-5 lg:col-span-2">
                <header className="flex items-center justify-between">
                  <div>
                    <h2 className="font-heading text-[17px] font-bold">Full-call score history</h2>
                    <p className="text-[12.5px] text-muted-foreground">
                      Latest 50 full calls, including historical scores; mixed sessions are not proof of improvement
                    </p>
                  </div>
                  {d.completed >= 2 ? (
                    <Badge variant={d.improvement >= 0 ? "secondary" : "destructive"}>
                      {d.improvement >= 0 ? (
                        <TrendingUp className="size-3.5" />
                      ) : (
                        <TrendingDown className="size-3.5" />
                      )}
                      {d.improvement > 0 ? "+" : ""}
                      {d.improvement} pts
                    </Badge>
                  ) : null}
                </header>
                <div className="mt-5 h-[240px]" data-testid="dashboard-trend-chart">
                  {d.trend.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={d.trend} margin={{ left: -18, right: 8, top: 8 }}>
                        <defs>
                          <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#2563EB" stopOpacity={0.28} />
                            <stop offset="100%" stopColor="#2563EB" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke="#E2E8F0" vertical={false} />
                        <XAxis
                          dataKey="label"
                          tick={{ fontSize: 12, fill: "#64748B" }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={{ fontSize: 12, fill: "#64748B" }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#E2E8F0" }}
                          formatter={(v) => [`${String(v)}/100`, "Score"]}
                          labelFormatter={(l, p) => {
                            const point = p?.[0]?.payload as { exercise_name?: string } | undefined;
                            return `${String(l)} · ${point?.exercise_name ?? ""}`;
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="score"
                          stroke="#2563EB"
                          strokeWidth={2.5}
                          fill="url(#tg)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="grid h-full place-items-center text-[13px] text-muted-foreground">
                      Your score trend appears after your first graded call.
                    </div>
                  )}
                </div>
              </section>

              <section
                className="rounded-lg border border-border bg-[#0F172A] p-5 text-slate-100"
                data-testid="dashboard-recommendation"
              >
                <h2 className="font-heading text-[13px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Recommended training
                </h2>
                <div className="mt-4 font-heading text-[22px] font-extrabold leading-tight">
                  {d.recommendation.exercise_name}
                </div>
                <div className="mt-2 flex items-center gap-2 text-[12.5px] text-slate-400">
                  Level {d.recommendation.difficulty} · {d.recommendation.difficulty_name}
                </div>
                <p className="mt-4 text-[13.5px] leading-relaxed text-slate-300">
                  {d.recommendation.reason}
                </p>
                <Link
                  to={`/learn/${d.recommendation.exercise_id}?difficulty=${d.recommendation.difficulty}`}
                  data-testid="dashboard-recommendation-start"
                  className="mt-6 inline-flex items-center gap-1.5 rounded-md bg-white px-4 py-2 text-[13.5px] font-semibold text-[#0F172A] transition-colors hover:bg-slate-200"
                >
                  Run this exercise
                  <ArrowUpRight className="size-4" />
                </Link>
                <div className="mt-6 border-t border-slate-800 pt-4 text-[12px] text-slate-400">
                  Difficulty unlocked: Level {d.unlocked_difficulty} · Highest attempted: Level{" "}
                  {d.difficulty_reached}
                </div>
              </section>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Skill diagnostic</h2>
                {d.skills.length ? (
                  <>
                    <div className="mt-4 grid gap-3">
                      {d.strongest_skill ? (
                        <div className="rounded-md bg-emerald-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
                            Strongest
                          </div>
                          <div className="mt-1 font-heading text-[16px] font-bold text-emerald-900">
                            {d.strongest_skill.category} · {d.strongest_skill.average}
                          </div>
                        </div>
                      ) : null}
                      {d.weakest_skill ? (
                        <div className="rounded-md bg-red-50 p-3">
                          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red-700">
                            Needs work
                          </div>
                          <div className="mt-1 font-heading text-[16px] font-bold text-red-900">
                            {d.weakest_skill.category} · {d.weakest_skill.average}
                          </div>
                        </div>
                      ) : null}
                    </div>
                    <div className="mt-4 divide-y divide-border">
                      {d.skills.slice(0, 6).map((s) => (
                        <SkillBar
                          key={s.category}
                          category={s.category}
                          score={s.average}
                          attempts={s.attempts}
                          testid={`dashboard-skill-${s.category.toLowerCase().replace(/\s+/g, "-")}`}
                        />
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="mt-4 text-[13px] text-muted-foreground">
                    Skill scores appear once you finish a simulation.
                  </p>
                )}
              </section>

              <section className="rounded-lg border border-border bg-card p-5 lg:col-span-2">
                <div className="flex items-center justify-between">
                  <h2 className="font-heading text-[17px] font-bold">Recent calls</h2>
                  <Link
                    to="/history"
                    className="text-[13px] font-medium text-primary"
                    data-testid="dashboard-view-history"
                  >
                    View all
                  </Link>
                </div>
                {d.recent.length ? (
                  <div className="mt-4 divide-y divide-border" data-testid="dashboard-recent-list">
                    {d.recent.map((s) => (
                      <Link
                        key={s.id}
                        to={`/scorecard/${s.id}`}
                        data-testid={`dashboard-recent-${s.id}`}
                        className="flex items-center gap-4 py-3 transition-colors hover:bg-secondary/60"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="truncate font-medium">{s.exercise_name}</div>
                          <div className="truncate text-[12.5px] text-muted-foreground">
                            {s.prospect_name} · {s.company} · {formatDuration(s.duration_seconds)}
                          </div>
                        </div>
                        <DifficultyPips level={s.difficulty} />
                        <div
                          className={cn(
                            "w-10 text-right font-mono text-[15px] font-semibold",
                            s.overall_score !== null ? scoreTone(s.overall_score) : "text-muted-foreground",
                          )}
                        >
                          {s.overall_score ?? "—"}
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4">
                    <EmptyState
                      testid="dashboard-empty-recent"
                      title="No simulations yet"
                      body="Run a five-minute cold call against a Developing-level prospect and get your first scored debrief."
                      action={
                        <Link
                          to="/learn/cold-call?difficulty=2"
                          data-testid="dashboard-empty-cta"
                          className={cn(buttonVariants(), "font-semibold")}
                        >
                          Start Your First Simulation
                        </Link>
                      }
                    />
                  </div>
                )}
              </section>
            </div>

            <section className="mt-6 rounded-lg border border-border bg-card p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-heading text-[17px] font-bold">Progress snapshot</h2>
                <div className="flex items-center gap-3">
                  <ScoreRing
                    score={d.average_score}
                    size={72}
                    label="Avg"
                    testid="dashboard-avg-ring"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {d.exercise_stats.length ? (
                  d.exercise_stats.map((e) => (
                    <div
                      key={e.exercise_id}
                      className="rounded-md border border-border p-3"
                      data-testid={`dashboard-exercise-stat-${e.exercise_id}`}
                    >
                      <div className="text-[13px] font-semibold">{e.exercise_name}</div>
                      <div className="mt-1 text-[12px] text-muted-foreground">
                        {e.attempts} reps · avg {e.average} · best {e.best}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    Per-exercise performance appears after your first call.
                  </p>
                )}
              </div>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

/** Zero-setup entry point: one click starts a pre-configured cold call so a
 * first-time user (or a judge) reaches the core loop in seconds. */
function DemoLaunch() {
  const launch = useDemoLaunch();

  return (
    <section
      className="mt-6 flex flex-wrap items-center gap-5 rounded-xl border border-[#1E293B] bg-[#0F172A] p-6 text-slate-100"
      data-testid="demo-launch-card"
    >
      <div className="min-w-0 flex-1">
        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
          No setup required
        </span>
        <h2 className="mt-2 font-heading text-[21px] font-extrabold tracking-[-0.01em]">
          Try a 2-minute demo call
        </h2>
        <p className="mt-1.5 max-w-xl text-[13.5px] leading-relaxed text-slate-400">
          Cold call Jordan Miller at Level 2. Review a short brief, choose voice or text, then get coaching. Aim for two minutes; there is no forced time limit.
        </p>
      </div>
      <Button
        size="lg"
        onClick={() => launch.mutate()}
        disabled={launch.isPending}
        className="bg-slate-100 font-semibold text-slate-900 hover:bg-white"
        data-testid="demo-launch-button"
      >
        {launch.isPending ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Dialling Jordan…
          </>
        ) : (
          <>
            <Zap className="size-4" />
            Start the demo call
          </>
        )}
      </Button>
    </section>
  );
}

/** RepForge Readiness Score: weighted competency coverage, not an average of scores. */
function ReadinessCard({ r }: { r: Readiness }) {
  return (
    <section
      className="mt-6 grid gap-6 rounded-xl border border-border bg-card p-6 lg:grid-cols-[auto_1fr]"
      data-testid="readiness-card"
    >
      <div className="flex flex-col items-center">
        <ScoreRing score={r.score} label="Practice" testid="readiness-score" />
        <span className="mt-2 rounded-full bg-secondary px-3 py-1 text-[12px] font-semibold" data-testid="readiness-label">
          {r.label}
        </span>
      </div>
      <div>
        <h2 className="font-heading text-[19px] font-bold">Assessed practice & coverage</h2>
        <p className="mt-1 text-[13.5px] text-muted-foreground">
          Weighted average of assessed skills from unaided evidence-validated full calls. Missing skills are unassessed, not failed. {r.covered} of {r.total_weighted} skills covered. This is not a validated real-world qualification.
        </p>
        <div className="mt-4 grid gap-x-6 gap-y-1 sm:grid-cols-2" data-testid="readiness-breakdown">
          {r.categories.map((c) => (
            <div
              key={c.category}
              className="flex items-center gap-3 py-1"
              data-testid={`readiness-${c.category.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <span className="w-[150px] shrink-0 truncate text-[13px]">{c.category}</span>
              <span className="font-mono text-[10.5px] text-muted-foreground">{c.weight}%</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary">
                <div
                  className={cn("h-full rounded-full", c.attempts ? "bg-primary" : "bg-slate-300")}
                  style={{ width: `${c.score ?? 0}%` }}
                />
              </div>
              <span
                className={cn(
                  "w-8 text-right font-mono text-[12.5px] font-semibold",
                  c.score !== null ? scoreTone(c.score) : "text-muted-foreground",
                )}
              >
                {c.attempts ? c.score : "—"}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-md bg-secondary p-3.5 text-[13px]" data-testid="readiness-recommendation">
          <span className="font-semibold">Biggest opportunity: </span>
          {r.recommendation}
        </div>
      </div>
    </section>
  );
}
