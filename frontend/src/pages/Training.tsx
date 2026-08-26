import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, GraduationCap, Lock, Shuffle, Target, User, Building2, Info, Loader2, Video, PresentationIcon, Users2 } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { getUserId } from "@/lib/profile";
import type {
  LearningStage,
  UserProfile,
  Dashboard as DashboardData,
  Difficulty,
  Exercise,
  ScenarioBrief,
  Simulation,
} from "@/lib/types";
import AppShell from "@/components/AppShell";
import Journeys from "@/components/Journeys";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const COMING_SOON = [
  {
    id: "zoom-calls",
    name: "Zoom video calls",
    icon: Video,
    blurb:
      "Run the simulation on camera: the prospect appears on video, and you get scored on eye contact, presence and the pauses you leave.",
  },
  {
    id: "screen-share-demo",
    name: "Screen-share demos",
    icon: PresentationIcon,
    blurb:
      "Share a live deck or product screen while the prospect interrupts with questions — graded on narration and handling derailments.",
  },
  {
    id: "multi-stakeholder",
    name: "Multi-stakeholder calls",
    icon: Users2,
    blurb:
      "Two or three AI buyers on one call — an economic buyer, a champion and a skeptic — so you practise managing the room.",
  },
];

export default function Training() {  const userId = getUserId();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [exerciseId, setExerciseId] = useState(params.get("exercise") ?? "cold-call");
  const [level, setLevel] = useState(Number(params.get("difficulty") ?? 2) || 2);
  const [scenarioIdx, setScenarioIdx] = useState(0);

  const { data: exercises } = useQuery({
    queryKey: ["exercises"],
    queryFn: () => apiGet<Exercise[]>("/exercises"),
    retry: false,
  });
  const { data: difficulties } = useQuery({
    queryKey: ["difficulties"],
    queryFn: () => apiGet<Difficulty[]>("/difficulties"),
    retry: false,
  });
  const { data: scenarios, isLoading: loadingScenarios } = useQuery({
    queryKey: ["scenarios", exerciseId],
    queryFn: () => apiGet<ScenarioBrief[]>(`/exercises/${exerciseId}/scenarios`),
    retry: false,
  });
  const { data: stages } = useQuery({
    queryKey: ["stages"],
    queryFn: () => apiGet<LearningStage[]>("/stages"),
    retry: false,
  });
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => apiGet<UserProfile>(`/users/${userId}`),
    enabled: Boolean(userId),
    retry: false,
  });
  const { data: dash } = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => apiGet<DashboardData>(`/users/${userId}/dashboard`),
    enabled: Boolean(userId),
    retry: false,
  });

  const exercise = useMemo(
    () => exercises?.find((e) => e.id === exerciseId),
    [exercises, exerciseId],
  );
  const difficulty = difficulties?.find((d) => d.level === level);
  const brief = scenarios && scenarios.length ? scenarios[scenarioIdx % scenarios.length] : undefined;
  const unlocked = dash?.unlocked_difficulty ?? 2;
  // Only treat a skill as locked once we actually know the rep's training record —
  // otherwise the button flashes disabled while the profile is still loading.
  const gateKnown = Boolean(user);
  const trained = Boolean(user?.trained_skills?.includes(exerciseId));
  const locked = gateKnown && !trained;

  useEffect(() => {
    setParams({ exercise: exerciseId, difficulty: String(level) }, { replace: true });
  }, [exerciseId, level, setParams]);

  const start = useMutation({
    mutationFn: () =>
      apiPost<Simulation>("/simulations", {
        user_id: userId,
        exercise_id: exerciseId,
        difficulty: level,
        scenario_id: brief?.id,
      }),
    onSuccess: (sim) => navigate(`/simulation/${sim.id}`),
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not start the simulation. Please try again.";
      toast.error(detail);
    },
  });

  if (!userId) return <Navigate to="/" replace />;

  return (
    <AppShell>
      <div data-testid="training-page">
        <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">
          RepForge Academy
        </h1>
        <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
          Every skill runs the full loop: <span className="font-semibold text-foreground">Learn → Prepare → Simulate → Coaching → Retry</span>. Some
          scenario information is deliberately withheld — you have to earn it in conversation.
        </p>

        <section className="mt-8" data-testid="journeys-section">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-heading text-[19px] font-extrabold">Prospect journeys</h2>
              <p className="mt-1 max-w-2xl text-[13.5px] text-muted-foreground">
                Recurring characters across several exercises. They remember what you discussed last
                time — and they will tell you if you ask something twice.
              </p>
            </div>
            <span className="text-[12.5px] text-muted-foreground">
              Runs at Level {level} · {difficulty?.name}
            </span>
          </div>
          <div className="mt-4">
            <Journeys difficulty={level} />
          </div>
        </section>

        <section className="mt-10" data-testid="coming-soon-section">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-heading text-[19px] font-extrabold">On the roadmap</h2>
              <p className="mt-1 max-w-2xl text-[13.5px] text-muted-foreground">
                The same evaluation engine, extended to the channels modern sellers actually work in.
              </p>
            </div>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {COMING_SOON.map((c) => (
              <div
                key={c.id}
                data-testid={`coming-soon-${c.id}`}
                className="rounded-lg border border-dashed border-border bg-secondary/40 p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="flex items-center gap-2 font-heading text-[15px] font-bold">
                    <c.icon className="size-4 text-muted-foreground" />
                    {c.name}
                  </span>
                  <span className="rounded-full bg-[#0F172A] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-white">
                    Coming soon
                  </span>
                </div>
                <p className="mt-2 text-[12.5px] leading-snug text-muted-foreground">{c.blurb}</p>
              </div>
            ))}
          </div>
        </section>

        <h2 className="mt-10 font-heading text-[19px] font-extrabold">Skill library</h2>        <p className="mt-1 text-[13.5px] text-muted-foreground">
          Follow the recommended order — each stage builds on the one before it.
        </p>

        <div className="mt-4 grid gap-6 lg:grid-cols-[1.25fr_1fr]">
          <div>
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              1 · Choose a skill
            </h2>
            <div className="mt-3 space-y-6" data-testid="exercise-grid">
              {(stages ?? []).map((st) => (
                <div key={st.id} data-testid={`stage-${st.id}`}>
                  <div className="flex items-baseline gap-2.5">
                    <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[#0F172A] font-mono text-[11px] font-bold text-white">
                      {st.order}
                    </span>
                    <div>
                      <div className="font-heading text-[15px] font-bold">{st.name}</div>
                      <p className="text-[12.5px] text-muted-foreground">{st.goal}</p>
                    </div>
                  </div>
                  <div className="mt-2.5 grid gap-3 sm:grid-cols-2">
                    {st.exercise_ids.map((eid) => {
                      const ex = exercises?.find((e) => e.id === eid);
                      if (!ex) return null;
                      const active = ex.id === exerciseId;
                      return (
                        <button
                          key={ex.id}
                          type="button"
                          onClick={() => {
                            setExerciseId(ex.id);
                            setScenarioIdx(0);
                          }}
                          data-testid={`exercise-card-${ex.id}`}
                          className={cn(
                            "rounded-lg border p-4 text-left transition-colors",
                            active
                              ? "border-primary bg-accent"
                              : "border-border bg-card hover:border-slate-300",
                          )}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-heading text-[15px] font-bold">{ex.name}</span>
                            <span className="font-mono text-[11px] text-muted-foreground">
                              ~{ex.duration_min}m
                            </span>
                          </div>
                          <p className="mt-1.5 text-[12.5px] leading-snug text-muted-foreground">
                            {ex.tagline}
                          </p>
                          {user?.trained_skills?.includes(ex.id) ? (
                            <div
                              className="mt-2 flex items-center gap-1 text-[11px] font-semibold text-emerald-700"
                              data-testid={`exercise-trained-${ex.id}`}
                            >
                              <GraduationCap className="size-3" />
                              Training complete
                            </div>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
              {!exercises || !stages
                ? Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-32 animate-pulse rounded-lg bg-secondary" />
                  ))
                : null}
            </div>

            <h2 className="mt-8 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              2 · Choose difficulty
            </h2>
            <div className="mt-3 space-y-2" data-testid="difficulty-list">
              {(difficulties ?? []).map((d) => {
                const active = d.level === level;
                const locked = d.level > unlocked;
                return (
                  <button
                    key={d.level}
                    type="button"
                    data-testid={`difficulty-option-${d.level}`}
                    onClick={() => {
                      setLevel(d.level);
                      if (locked)
                        toast.info(
                          `Level ${d.level} is above your unlocked tier — expect a genuinely hard buyer.`,
                        );
                    }}
                    className={cn(
                      "flex w-full items-start gap-4 rounded-lg border p-3.5 text-left transition-colors",
                      active
                        ? "border-primary bg-accent"
                        : "border-border bg-card hover:border-slate-300",
                    )}
                  >
                    <span
                      className={cn(
                        "grid size-8 shrink-0 place-items-center rounded-md font-heading text-[14px] font-bold",
                        active ? "bg-[#0F172A] text-white" : "bg-secondary text-slate-600",
                      )}
                    >
                      {d.level}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2 font-heading text-[14.5px] font-bold">
                        {d.name}
                        <span className="text-[12px] font-normal text-muted-foreground">
                          {d.subtitle}
                        </span>
                        {locked ? (
                          <span className="flex items-center gap-1 text-[11px] text-amber-700">
                            <Lock className="size-3" /> unlocks at {d.unlock_xp} XP
                          </span>
                        ) : null}
                      </span>
                      <span className="mt-1 block text-[12.5px] leading-snug text-muted-foreground">
                        {d.behavior}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <aside className="lg:sticky lg:top-24 lg:self-start">
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              3 · Pre-call brief
            </h2>
            <div
              className="mt-3 overflow-hidden rounded-xl border border-border bg-card"
              data-testid="pre-call-brief"
            >
              <div className="border-b border-border bg-[#0F172A] p-5 text-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                    {exercise?.name ?? "Exercise"}
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className="rounded-full bg-slate-800 px-2.5 py-1 text-[11px] font-semibold"
                      data-testid="brief-difficulty"
                    >
                      Level {level} · {difficulty?.name}
                    </span>
                    {scenarios && scenarios.length > 1 ? (
                      <button
                        type="button"
                        onClick={() => setScenarioIdx((i) => i + 1)}
                        data-testid="brief-shuffle-scenario"
                        className="flex items-center gap-1 rounded-full bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-slate-300 transition-colors hover:bg-slate-700"
                      >
                        <Shuffle className="size-3" />
                        New scenario
                      </button>
                    ) : null}
                  </div>
                </div>
                <h3 className="mt-4 font-heading text-[20px] font-extrabold leading-snug">
                  {brief ? `You are selling ${brief.product}.` : "Loading scenario…"}
                </h3>
              </div>

              {loadingScenarios || !brief ? (
                <div className="space-y-3 p-5" data-testid="brief-loading">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-4 animate-pulse rounded bg-secondary" />
                  ))}
                </div>
              ) : (
                <div className="divide-y divide-border">
                  <section className="p-5">
                    <BriefLabel icon={User} text="Prospect" />
                    <div className="mt-2 font-heading text-[16px] font-bold" data-testid="brief-prospect">
                      {brief.prospect_name}
                    </div>
                    <div className="text-[13px] text-muted-foreground">
                      {brief.prospect_role} · {brief.company}
                    </div>
                    <div className="mt-1 flex items-center gap-1.5 text-[12.5px] text-muted-foreground">
                      <Building2 className="size-3.5" />
                      {brief.company_size} · {brief.industry}
                    </div>
                    <div className="mt-2 text-[12.5px] text-muted-foreground">
                      Mood: <span className="font-medium text-foreground">{brief.mood}</span>
                    </div>
                  </section>

                  <section className="p-5">
                    <BriefLabel icon={Info} text="Known information" />
                    <p className="mt-2 text-[13.5px] leading-relaxed" data-testid="brief-known">
                      {brief.known}
                    </p>
                  </section>

                  <section className="p-5">
                    <BriefLabel icon={Target} text="Your objective" />
                    <p className="mt-2 text-[13.5px] leading-relaxed" data-testid="brief-objective">
                      {brief.objective}
                    </p>
                  </section>

                  <section className="bg-secondary/60 p-5">
                    <p className="text-[12.5px] leading-relaxed text-muted-foreground">
                      This prospect knows things about their business that you do not. Budget,
                      timeline, decision makers and the real pain are hidden — the only way to reach
                      them is good questions.
                    </p>
                  </section>
                </div>
              )}

              <div className="border-t border-border p-5">
                <Link
                  to={`/learn/${exerciseId}?difficulty=${level}`}
                  className={cn(buttonVariants({ size: "lg" }), "w-full font-semibold")}
                  data-testid="brief-open-training"
                >
                  <GraduationCap className="size-4" />
                  Learn this skill first
                </Link>
                <Button
                  size="lg"
                  variant="outline"
                  className="mt-2 w-full font-semibold"
                  onClick={() => start.mutate()}
                  disabled={start.isPending || !brief || locked}
                  data-testid="start-simulation-button"
                >
                  {start.isPending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Connecting you to {brief?.prospect_name ?? "the prospect"}…
                    </>
                  ) : (
                    <>
                      Skip training, start the call
                      <ArrowRight className="size-4" />
                    </>
                  )}
                </Button>
                <p className="mt-2.5 text-center text-[12px] text-muted-foreground">
                  {locked
                    ? "New skill: work through the training once and direct practice unlocks permanently."
                    : "Skill unlocked — start the call directly, or re-read the training any time."}
                </p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function BriefLabel({
  icon: Icon,
  text,
}: {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
}) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
      <Icon className="size-3.5" />
      {text}
    </div>
  );
}
