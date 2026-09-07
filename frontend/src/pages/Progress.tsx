import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TrendingDown, TrendingUp } from "lucide-react";
import { apiGet } from "@/lib/api";
import { formatDuration, getUserId, scoreTone } from "@/lib/profile";
import type { Dashboard as DashboardData } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { EmptyState, SkillBar, StatCard } from "@/components/Metrics";
import AttemptComparison from "@/components/AttemptComparison";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Progress() {
  const userId = getUserId();
  const [compareId, setCompareId] = useState<string | null>(null);
  const { data: d, isLoading } = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => apiGet<DashboardData>(`/users/${userId}/dashboard`),
    enabled: Boolean(userId),
    retry: false,
  });

  if (!userId) return <Navigate to="/" replace />;

  return (
    <AppShell>
      <div data-testid="progress-page">
        <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">
          Progress & competency
        </h1>
        <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
          Review score history and skill coverage. Comparable assessments share a scenario, difficulty, rubric and assistance setting; mixed scores are not proof of improvement.
        </p>

        {isLoading ? (
          <div className="mt-8 grid gap-4 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-secondary" />
            ))}
          </div>
        ) : null}

        {d && d.completed === 0 ? (
          <div className="mt-8">
            <EmptyState
              testid="progress-empty"
              title="No training data yet"
              body="Complete your first simulation and this page starts tracking every competency, exercise type and difficulty tier."
              action={
                <Link
                  to="/learn/cold-call?difficulty=2"
                  className={cn(buttonVariants(), "font-semibold")}
                  data-testid="progress-empty-cta"
                >
                  Start Your First Simulation
                </Link>
              }
            />
          </div>
        ) : null}

        {d && d.completed > 0 ? (
          <>
            <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                testid="progress-stat-reps"
                label="Reps completed"
                value={String(d.completed)}
                hint={`${formatDuration(d.total_practice_seconds)} on live calls`}
              />
              <StatCard
                testid="progress-stat-avg"
                label="Average score"
                value={String(d.average_score)}
                tone={scoreTone(d.average_score)}
                hint={`Best ${d.personal_best}`}
              />
              <StatCard
                testid="progress-stat-improvement"
                label="Comparable change"
                value={`${d.improvement > 0 ? "+" : ""}${d.improvement}`}
                tone={d.improvement >= 0 ? "text-emerald-600" : "text-red-600"}
                hint="Same-scenario unaided assessments only"
              />
              <StatCard
                testid="progress-stat-tier"
                label="Difficulty reached"
                value={`L${d.difficulty_reached}`}
                hint={`Unlocked through Level ${d.unlocked_difficulty}`}
              />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Score history</h2>
                <div className="mt-4 h-[260px]" data-testid="progress-line-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={d.trend} margin={{ left: -20, right: 8, top: 8 }}>
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
                        contentStyle={{ fontSize: 12, borderRadius: 8 }}
                        formatter={(v) => [`${String(v)}/100`, "Score"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#2563EB"
                        strokeWidth={2.5}
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Competency radar</h2>
                <div className="mt-4 h-[260px]" data-testid="progress-radar-chart">
                  {d.skills.length >= 3 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={d.skills.slice(0, 8)} outerRadius="72%">
                        <PolarGrid stroke="#E2E8F0" />
                        <PolarAngleAxis
                          dataKey="category"
                          tick={{ fontSize: 11, fill: "#475569" }}
                        />
                        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                        <Radar
                          dataKey="average"
                          stroke="#2563EB"
                          fill="#2563EB"
                          fillOpacity={0.22}
                        />
                        <Tooltip formatter={(v) => `${String(v)}/100`} />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="grid h-full place-items-center text-[13px] text-muted-foreground">
                      Complete a few more calls to populate the radar.
                    </div>
                  )}
                </div>
              </section>
            </div>

            <section className="mt-6 rounded-xl border border-border bg-card p-5" data-testid="progress-comparison">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-heading text-[17px] font-bold">Attempt comparison</h2>
                  <p className="text-[12.5px] text-muted-foreground">
                    Evidence-validated comparable full calls only. Coached moment drills stay separate.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2" data-testid="comparison-exercise-picker">
                  {d.exercise_stats.map((e) => (
                    <button
                      key={e.exercise_id}
                      type="button"
                      onClick={() => setCompareId(e.exercise_id)}
                      data-testid={`compare-${e.exercise_id}`}
                      className={cn(
                        "rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors",
                        (compareId ?? d.exercise_stats[0]?.exercise_id) === e.exercise_id
                          ? "bg-[#0F172A] text-white"
                          : "bg-secondary text-slate-600",
                      )}
                    >
                      {e.exercise_name} ({e.attempts})
                    </button>
                  ))}
                </div>
              </div>
              <div className="mt-4">
                <AttemptComparison
                  userId={userId}
                  exerciseId={compareId ?? d.exercise_stats[0]?.exercise_id ?? "cold-call"}
                />
              </div>
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Assessed skill averages & score history</h2>
                <div className="mt-4 divide-y divide-border" data-testid="progress-skills">
                  {d.skills.map((s) => (
                    <div key={s.category} className="flex items-center gap-4">
                      <div className="flex-1">
                        <SkillBar
                          category={s.category}
                          score={s.average}
                          attempts={s.attempts}
                          testid={`progress-skill-${s.category.toLowerCase().replace(/\s+/g, "-")}`}
                        />
                      </div>
                      <span
                        className={cn(
                          "flex w-16 items-center justify-end gap-1 font-mono text-[12.5px] font-semibold",
                          s.trend >= 0 ? "text-emerald-600" : "text-red-600",
                        )}
                      >
                        {s.trend >= 0 ? (
                          <TrendingUp className="size-3.5" />
                        ) : (
                          <TrendingDown className="size-3.5" />
                        )}
                        {s.trend > 0 ? "+" : ""}
                        {s.trend}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Performance by exercise</h2>
                <div className="mt-4 space-y-2" data-testid="progress-exercises">
                  {d.exercise_stats.map((e) => (
                    <div
                      key={e.exercise_id}
                      className="flex items-center justify-between rounded-md border border-border p-3"
                      data-testid={`progress-exercise-${e.exercise_id}`}
                    >
                      <div>
                        <div className="text-[14px] font-semibold">{e.exercise_name}</div>
                        <div className="text-[12px] text-muted-foreground">
                          {e.attempts} reps · best {e.best}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={cn("font-mono text-[15px] font-bold", scoreTone(e.average))}>
                          {e.average}
                        </span>
                        <Link
                          to={`/learn/${e.exercise_id}?difficulty=${d.unlocked_difficulty}`}
                          className={cn(buttonVariants({ variant: "outline", size: "xs" }))}
                          data-testid={`progress-practice-${e.exercise_id}`}
                        >
                          Practise
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-md bg-[#0F172A] p-4 text-slate-100">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                    Next up
                  </div>
                  <div className="mt-1.5 font-heading text-[16px] font-bold">
                    {d.recommendation.exercise_name} · Level {d.recommendation.difficulty}
                  </div>
                  <p className="mt-2 text-[13px] text-slate-300">{d.recommendation.reason}</p>
                </div>
              </section>
            </div>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
