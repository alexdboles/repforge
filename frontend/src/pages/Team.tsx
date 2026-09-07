import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BellRing, Clock, Info, TrendingDown, TrendingUp, Trophy, Users } from "lucide-react";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { toast } from "sonner";
import { formatDuration, getUserId, scoreTone } from "@/lib/profile";
import type { Exercise, TeamView, UserProfile } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { EmptyState, SkillBar, StatCard } from "@/components/Metrics";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
import WorkspaceAccess from '@/components/WorkspaceAccess';

export default function Team() {
  const userId = getUserId();
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => apiGet<UserProfile>(`/users/${userId}`),
    enabled: Boolean(userId),
    retry: false,
  });
  const qc = useQueryClient();
  const [assignTo, setAssignTo] = useState<string | null>(null);
  const [assignExercise, setAssignExercise] = useState("objection-handling");
  const [assignLevel, setAssignLevel] = useState(3);
  const [assignNote, setAssignNote] = useState("");
  const [managerMinutes, setManagerMinutes] = useState(15);
  const activeOrg = user?.workspace_id ?? '';
  const canManage = Boolean(user && !user.is_guest && ['owner', 'admin', 'manager'].includes(user.workspace_role));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["team", activeOrg, managerMinutes],
    queryFn: () => apiGet<TeamView>(`/teams/${encodeURIComponent(activeOrg)}?manager_minutes=${managerMinutes}`),
    enabled: Boolean(activeOrg) && canManage,
    retry: false,
  });

  const { data: exercises } = useQuery({
    queryKey: ["exercises"],
    queryFn: () => apiGet<Exercise[]>("/exercises"),
    retry: false,
  });

  const assign = useMutation({
    mutationFn: () =>
      apiPost(`/assignments`, {
        user_id: assignTo,
        exercise_id: assignExercise,
        difficulty: assignLevel,
        note: assignNote,
        assigned_by: `${user?.name ?? "Manager"} (Manager)`,
        org: activeOrg,
      }),
    onSuccess: () => {
      toast.success("Training assigned");
      setAssignTo(null);
      setAssignNote("");
      qc.invalidateQueries({ queryKey: ["team", activeOrg] });
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not assign training.";
      toast.error(detail);
    },
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
              Only verified workspace members appear here. Reports and assignments require manager permission.
            </p>
          </div>
          <div>
            <label className="text-[12px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              Workspace ID
            </label>
            <Input
              value={activeOrg}
              readOnly
              className="mt-1.5 w-[240px]"
              data-testid="team-org-input"
            />
          </div>
        </div>

        {user ? <WorkspaceAccess user={user} /> : null}
        {user && !canManage ? <p data-testid='team-permission-note'>Team reports are restricted to managers. Your own practice remains available in History.</p> : null}

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
              title="Team report unavailable"
              body="Check your verified membership and manager permissions, then reload. Organisation names do not grant access."
              action={
                <Link to="/profile" className={cn(buttonVariants(), "font-semibold")} data-testid="team-empty-cta">
                  View my profile
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
                label="Comparable score change"
                value={`${data.team_improvement > 0 ? "+" : ""}${data.team_improvement}`}
                tone={data.team_improvement >= 0 ? "text-emerald-600" : "text-red-600"}
                hint="Last 14 UTC days vs previous 14; common scenario cohorts only"
              />
              <StatCard
                testid="team-stat-hours"
                label="Estimated manager hours"
                value={`${data.manager_hours_saved}h`}
                hint={`Full calls of 2+ minutes × ${managerMinutes} assumed minutes; not measured savings`}
              />
            </div>

            <label className='mt-4 flex flex-wrap items-center gap-3 text-sm' data-testid='manager-assumption-label'>Assumed manager minutes per full role-play<Input className='w-24' type='number' min={0} max={120} value={managerMinutes} onChange={e => setManagerMinutes(Math.min(120, Math.max(0, Number(e.target.value))))} data-testid='manager-minutes-assumption' /></label>

            {data.lapsed_members.length ? (
              <div
                className="mt-6 flex flex-wrap items-center gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4"
                data-testid="team-lapsed-banner"
              >
                <BellRing className="size-5 shrink-0 text-amber-700" />
                <div className="min-w-0 flex-1 text-[13.5px] text-amber-950">
                  <span className="font-semibold">
                    {data.lapsed_members.length} rep{data.lapsed_members.length > 1 ? "s" : ""} haven't
                    practised in 3+ days:{" "}
                  </span>
                  {data.lapsed_members.join(", ")}
                </div>
              </div>
            ) : null}

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
                      <TableHead />
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
                        <TableCell className="text-right">
                          <button
                            type="button"
                            onClick={() => {
                              setAssignTo(m.user_id);
                              if (m.weakest_skill) setAssignNote(`${m.weakest_skill} is your lowest category`);
                            }}
                            className="text-[12.5px] font-semibold text-primary"
                            data-testid={`assign-${m.user_id}`}
                          >
                            Assign
                          </button>
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

            {assignTo ? (
              <section
                className="mt-6 rounded-xl border border-primary/40 bg-accent p-5"
                data-testid="assign-panel"
              >
                <h2 className="font-heading text-[17px] font-bold">
                  Assign training to {data.members.find((m) => m.user_id === assignTo)?.name}
                </h2>
                <div className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr_1.4fr_auto]">
                  <div>
                    <span className="text-[12px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      Skill
                    </span>
                    <div className="mt-1.5 flex flex-wrap gap-1.5" data-testid="assign-exercises">
                      {(exercises ?? []).map((ex) => (
                        <button
                          key={ex.id}
                          type="button"
                          onClick={() => setAssignExercise(ex.id)}
                          data-testid={`assign-exercise-${ex.id}`}
                          className={cn(
                            "rounded-full px-2.5 py-1 text-[12px] font-semibold",
                            ex.id === assignExercise ? "bg-[#0F172A] text-white" : "bg-white text-slate-600",
                          )}
                        >
                          {ex.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-[12px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      Difficulty
                    </span>
                    <div className="mt-1.5 flex gap-1.5" data-testid="assign-difficulties">
                      {[1, 2, 3, 4, 5].map((l) => (
                        <button
                          key={l}
                          type="button"
                          onClick={() => setAssignLevel(l)}
                          data-testid={`assign-difficulty-${l}`}
                          className={cn(
                            "size-8 rounded-md text-[13px] font-bold",
                            l === assignLevel ? "bg-[#0F172A] text-white" : "bg-white text-slate-600",
                          )}
                        >
                          {l}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-[12px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      Note to the rep
                    </span>
                    <Input
                      value={assignNote}
                      onChange={(e) => setAssignNote(e.target.value)}
                      className="mt-1.5 bg-white"
                      data-testid="assign-note"
                    />
                  </div>
                  <div className="flex items-end gap-2">
                    <Button
                      onClick={() => assign.mutate()}
                      disabled={assign.isPending}
                      data-testid="assign-submit"
                      className="font-semibold"
                    >
                      {assign.isPending ? "Assigning…" : "Assign"}
                    </Button>
                    <Button variant="ghost" onClick={() => setAssignTo(null)} data-testid="assign-cancel">
                      Cancel
                    </Button>
                  </div>
                </div>
              </section>
            ) : null}

            <section className="mt-6 rounded-xl border border-border bg-card p-5" data-testid="assignment-tracking">
              <h2 className="font-heading text-[17px] font-bold">Assigned training</h2>
              <p className="text-[12.5px] text-muted-foreground">
                Completion is recorded automatically when the rep finishes that exercise.
              </p>
              <div className="mt-4 space-y-2">
                {data.assignments.length ? (
                  data.assignments.map((a) => (
                    <div
                      key={a.id}
                      className="flex flex-wrap items-center gap-3 rounded-lg border border-border p-3"
                      data-testid={`team-assignment-${a.id}`}
                    >
                      <span className="min-w-0 flex-1">
                        <span className="text-[13.5px] font-semibold">{a.user_name}</span>
                        <span className="ml-2 text-[13px] text-muted-foreground">
                          {a.exercise_name} · L{a.difficulty}
                        </span>
                        {a.note ? (
                          <span className="block text-[12px] text-muted-foreground">{a.note}</span>
                        ) : null}
                      </span>
                      {a.status === "completed" ? (
                        <span
                          className="text-[12.5px] font-semibold text-emerald-700"
                          data-testid={`team-assignment-done-${a.id}`}
                        >
                          Completed · {a.score}
                        </span>
                      ) : (
                        <Badge variant="outline">Pending</Badge>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-[13px] text-muted-foreground">
                    Nothing assigned yet — use Assign on any rep above.
                  </p>
                )}
              </div>
            </section>

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
                Verified workspace members only. Managers see summary scores, not private transcripts.
                Score history is practice evidence, not a validated qualification. Time savings are estimates, not measured customer outcomes.
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
