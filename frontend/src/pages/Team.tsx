import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Clock, Info, TrendingDown, TrendingUp, Trophy, Users } from "lucide-react";
import { apiGet } from "@/lib/api";
import { formatDuration, getUserId, scoreTone } from "@/lib/profile";
import type { TeamView, UserProfile } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { EmptyState, SkillBar, StatCard } from "@/components/Metrics";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export default function Team() {
  const userId = getUserId();
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => apiGet<UserProfile>(`/users/${userId}`),
    enabled: Boolean(userId),
    retry: false,
  });
  const [org, setOrg] = useState<string | null>(null);
  const activeOrg = org ?? user?.org ?? "";

  const { data, isLoading, isError } = useQuery({
    queryKey: ["team", activeOrg],
    queryFn: () => apiGet<TeamView>(`/teams/${encodeURIComponent(activeOrg)}`),
    enabled: Boolean(activeOrg),
    retry: false,
  });

  if (!userId) return <Navigate to="/" replace />;

  return (
    <AppShell>
      <div data-testid="team-page">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Badge variant="secondary">
              <Users className="size-3" />
              Manager preview
            </Badge>
            <h1 className="mt-2 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              Team performance
            </h1>
            <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
              Every rep who sets the same Organisation on their profile rolls up here — practice
              frequency, improvement, shared skill gaps and the coaching hours this replaces.
            </p>
          </div>
          <div>
            <label className="text-[12px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              Organisation
            </label>
            <Input
              value={activeOrg}
              onChange={(e) => setOrg(e.target.value)}
              className="mt-1.5 w-[240px]"
              data-testid="team-org-input"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="mt-8 grid gap-4 lg:grid-cols-4" data-testid="team-loading">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-secondary" />
            ))}
          </div>
        ) : null}

        {isError ? (
          <div className="mt-8">
            <EmptyState
              testid="team-empty"
              title={`No reps in "${activeOrg}" yet`}
              body="Set the same Organisation name on each rep's profile and their simulations roll up into this view. Change the organisation above to look at another team."
              action={
                <Link to="/profile" className={cn(buttonVariants(), "font-semibold")} data-testid="team-empty-cta">
                  Set my organisation
                </Link>
              }
            />
          </div>
        ) : null}

        {data ? (
          <>
            <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                testid="team-stat-members"
                label="Team members"
                value={String(data.members.length)}
                hint={`${data.total_reps} simulations completed`}
              />
              <StatCard
                testid="team-stat-average"
                label="Team average"
                value={data.team_average !== null ? String(data.team_average) : "—"}
                tone={data.team_average !== null ? scoreTone(data.team_average) : undefined}
                hint="Across all graded calls"
              />
              <StatCard
                testid="team-stat-improvement"
                label="Team improvement"
                value={`${data.team_improvement > 0 ? "+" : ""}${data.team_improvement}`}
                tone={data.team_improvement >= 0 ? "text-emerald-600" : "text-red-600"}
                hint="Latest half vs first half"
              />
              <StatCard
                testid="team-stat-hours"
                label="Manager hours saved"
                value={`${data.manager_hours_saved}h`}
                hint={`${data.total_reps} role-plays at 30 min each`}
              />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
              <section className="overflow-hidden rounded-xl border border-border bg-card">
                <div className="border-b border-border p-5">
                  <h2 className="font-heading text-[17px] font-bold">Reps</h2>
                  <p className="text-[12.5px] text-muted-foreground">
                    Readiness at a glance — who is practising, who is improving, where each rep is weak.
                  </p>
                </div>
                <Table data-testid="team-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rep</TableHead>
                      <TableHead>Sessions</TableHead>
                      <TableHead>Avg</TableHead>
                      <TableHead>Trend</TableHead>
                      <TableHead>Weakest skill</TableHead>
                      <TableHead>Last practice</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.members.map((m) => (
                      <TableRow key={m.user_id} data-testid={`team-row-${m.user_id}`}>
                        <TableCell>
                          <div className="font-medium">{m.name}</div>
                          <div className="text-[12px] text-muted-foreground">
                            {m.experience_level} · L{m.level} · {m.xp} XP
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-[13px]">
                          {m.reps}
                          <span className="ml-1.5 text-[11px] text-muted-foreground">
                            {formatDuration(m.practice_seconds)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              "font-mono text-[14px] font-bold",
                              m.average_score !== null ? scoreTone(m.average_score) : "text-muted-foreground",
                            )}
                          >
                            {m.average_score ?? "—"}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              "flex items-center gap-1 font-mono text-[12.5px] font-semibold",
                              m.improvement >= 0 ? "text-emerald-600" : "text-red-600",
                            )}
                          >
                            {m.improvement >= 0 ? (
                              <TrendingUp className="size-3.5" />
                            ) : (
                              <TrendingDown className="size-3.5" />
                            )}
                            {m.improvement > 0 ? "+" : ""}
                            {m.improvement}
                          </span>
                        </TableCell>
                        <TableCell className="text-[13px]">{m.weakest_skill ?? "—"}</TableCell>
                        <TableCell className="text-[12.5px] text-muted-foreground">
                          {m.last_practice_date ?? "Never"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </section>

              <div className="space-y-6">
                <section className="rounded-xl border border-border bg-card p-5">
                  <h2 className="font-heading text-[17px] font-bold">Shared skill gaps</h2>
                  <p className="text-[12.5px] text-muted-foreground">
                    Lowest-scoring competencies across the whole team — where group coaching pays off.
                  </p>
                  <div className="mt-4 divide-y divide-border" data-testid="team-skill-gaps">
                    {data.skill_gaps.length ? (
                      data.skill_gaps.map((s) => (
                        <SkillBar
                          key={s.category}
                          category={s.category}
                          score={s.average}
                          attempts={s.attempts}
                          testid={`team-gap-${s.category.toLowerCase().replace(/\s+/g, "-")}`}
                        />
                      ))
                    ) : (
                      <p className="py-2 text-[13px] text-muted-foreground">
                        Skill gaps appear once the team completes graded calls.
                      </p>
                    )}
                  </div>
                </section>

                <section className="rounded-xl border border-border bg-card p-5">
                  <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
                    <Trophy className="size-4 text-amber-600" />
                    Leaderboard
                  </h2>
                  <ol className="mt-4 space-y-2" data-testid="team-leaderboard">
                    {data.leaderboard.map((m, i) => (
                      <li
                        key={m.user_id}
                        className="flex items-center gap-3 rounded-md bg-secondary/60 px-3 py-2"
                        data-testid={`leaderboard-${i}`}
                      >
                        <span className="font-mono text-[12px] text-muted-foreground">{i + 1}</span>
                        <span className="min-w-0 flex-1 truncate text-[13.5px] font-medium">{m.name}</span>
                        <span className="text-[12px] text-muted-foreground">{m.reps} reps</span>
                        <span className={cn("font-mono text-[14px] font-bold", scoreTone(m.average_score ?? 0))}>
                          {m.average_score}
                        </span>
                      </li>
                    ))}
                    {!data.leaderboard.length ? (
                      <li className="text-[13px] text-muted-foreground">No graded calls yet.</li>
                    ) : null}
                  </ol>
                </section>
              </div>
            </div>

            <section className="mt-6 rounded-xl border border-border bg-card p-5">
              <h2 className="font-heading text-[17px] font-bold">Exercise coverage</h2>
              <p className="text-[12.5px] text-muted-foreground">
                Which skills the team is actually rehearsing — and which are being avoided.
              </p>
              <div className="mt-4 h-[240px]" data-testid="team-coverage-chart">
                {data.exercise_coverage.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.exercise_coverage} margin={{ left: -20, top: 8 }}>
                      <CartesianGrid stroke="#E2E8F0" vertical={false} />
                      <XAxis
                        dataKey="exercise_name"
                        tick={{ fontSize: 11, fill: "#64748B" }}
                        axisLine={false}
                        tickLine={false}
                        interval={0}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: "#64748B" }}
                        axisLine={false}
                        tickLine={false}
                        allowDecimals={false}
                      />
                      <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                      <Bar dataKey="attempts" fill="#2563EB" radius={[4, 4, 0, 0]} name="Reps" />
                      <Bar dataKey="average" fill="#94A3B8" radius={[4, 4, 0, 0]} name="Avg score" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="grid h-full place-items-center text-[13px] text-muted-foreground">
                    No completed exercises yet.
                  </div>
                )}
              </div>
            </section>

            <div
              className="mt-6 flex items-start gap-2.5 rounded-lg border border-dashed border-border bg-card p-4 text-[12.5px] leading-relaxed text-muted-foreground"
              data-testid="team-preview-note"
            >
              <Info className="mt-0.5 size-4 shrink-0" />
              <span>
                Manager preview: read-only aggregation over the existing rep data. Assigned training,
                invite-based membership and onboarding programmes are the next layer — the data model
                already supports them.
              </span>
            </div>

            <p className="mt-4 flex items-center gap-1.5 text-[12px] text-muted-foreground">
              <Clock className="size-3.5" />
              {formatDuration(data.total_practice_seconds)} of live conversation practice logged by this team.
            </p>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
