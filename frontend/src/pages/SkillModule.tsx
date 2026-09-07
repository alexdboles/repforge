import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Book,
  Building2,
  CheckCircle2,
  ClipboardList,
  Info,
  Loader2,
  Quote,
  Target,
  TriangleAlert,
  User,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { getUserId } from "@/lib/profile";
import type {
  UserProfile,
  Difficulty,
  Exercise,
  ScenarioBrief,
  Simulation,
  TrainingModule,
} from "@/lib/types";
import AppShell from "@/components/AppShell";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const STEPS = [
  { key: "learn", label: "Learn the skill", icon: Book },
  { key: "scenario", label: "Scenario briefing", icon: ClipboardList },
  { key: "prepare", label: "Pre-call prep", icon: Target },
] as const;

export default function SkillModule() {
  const { exerciseId = "cold-call" } = useParams();
  const userId = getUserId();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [step, setStep] = useState(0);
  const [level, setLevel] = useState(Number(params.get("difficulty") ?? 2) || 2);
  const [scenarioIdx, setScenarioIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});

  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => apiGet<UserProfile>(`/users/${userId}`),
    enabled: Boolean(userId),
    retry: false,
  });
  const markTrained = useMutation({
    mutationFn: () => apiPost<{ trained_skills: string[] }>(`/users/${userId}/trained/${exerciseId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["user", userId] }),
  });
  const trained = Boolean(user?.trained_skills?.includes(exerciseId));

  const { data: mod, isLoading: loadingModule } = useQuery({
    queryKey: ["curriculum", exerciseId],
    queryFn: () => apiGet<TrainingModule>(`/curriculum/${exerciseId}`),
    retry: false,
  });
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
  const { data: scenarios } = useQuery({
    queryKey: ["scenarios", exerciseId],
    queryFn: () => apiGet<ScenarioBrief[]>(`/exercises/${exerciseId}/scenarios`),
    retry: false,
  });

  const exercise = useMemo(
    () => exercises?.find((e) => e.id === exerciseId),
    [exercises, exerciseId],
  );
  const difficulty = difficulties?.find((d) => d.level === level);
  const brief =
    scenarios && scenarios.length ? scenarios[scenarioIdx % scenarios.length] : undefined;
  const sheet = brief?.product_sheet ?? null;

  const rememberList = useMemo(
    () => (brief?.things_to_remember ?? []).filter(Boolean),
    [brief?.things_to_remember],
  );

  const start = useMutation({
    mutationFn: () =>
      apiPost<Simulation>("/simulations", {
        user_id: userId,
        exercise_id: exerciseId,
        difficulty: level,
        scenario_id: brief?.id,
        mode: "guided",
        assignment_id: params.get('assignment'),
      }),
    onSuccess: (sim) => navigate(`/simulation/${sim.id}`),
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not start the simulation.";
      toast.error(detail);
    },
  });

  if (!userId) return <Navigate to="/" replace />;

  const goto = (i: number) => {
    // Reaching the prep step is what unlocks this skill for direct practice later.
    if (i >= 2 && !trained && !markTrained.isPending) markTrained.mutate();
    setStep(i);
    setParams({ difficulty: String(level), ...(params.get('assignment') ? { assignment: params.get('assignment')! } : {}) }, { replace: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AppShell>
      <div data-testid="skill-module-page">
        <Link
          to="/training"
          className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground hover:text-foreground"
          data-testid="module-back-library"
        >
          <ArrowLeft className="size-3.5" />
          Training library
        </Link>

        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <Badge variant="secondary">Guided training</Badge>
            <h1 className="mt-2 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              {mod?.title ?? exercise?.name ?? "Training"}
            </h1>
            <p className="mt-1.5 text-[14.5px] text-muted-foreground">
              {mod?.promise ?? exercise?.tagline}
            </p>
          </div>
          <div className="text-right">
            <Button
              variant="outline"
              onClick={() => goto(2)}
              data-testid="module-skip-to-call"
              className="font-semibold"
            >
              {trained ? "Skip to the call" : "Jump to pre-call prep"}
              <ArrowRight className="size-4" />
            </Button>
            <p className="mt-1.5 text-[11.5px] text-muted-foreground" data-testid="module-gate-status">
              {trained
                ? "Skill unlocked — you can start this call directly from the library"
                : "First time on this skill: open the prep step to unlock direct practice"}
            </p>
          </div>
        </div>

        <nav className="mt-7 flex flex-wrap gap-2" data-testid="module-steps">
          {STEPS.map((s, i) => (
            <button
              key={s.key}
              type="button"
              onClick={() => goto(i)}
              data-testid={`module-step-${s.key}`}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3.5 py-2 text-[13px] font-semibold transition-colors",
                i === step
                  ? "border-primary bg-accent text-accent-foreground"
                  : "border-border bg-card text-muted-foreground hover:border-slate-300",
              )}
            >
              <s.icon className="size-3.5" />
              {i + 1}. {s.label}
            </button>
          ))}
        </nav>

        {loadingModule ? (
          <div className="mt-8 grid place-items-center py-16" data-testid="module-loading">
            <Loader2 className="size-5 animate-spin text-primary" />
          </div>
        ) : null}

        {mod && step === 0 ? (
          <div className="mt-7 grid gap-6 lg:grid-cols-[1.35fr_1fr]" data-testid="module-learn">
            <div className="space-y-6">
              <section className="rounded-xl border border-border bg-card p-6">
                <h2 className="font-heading text-[19px] font-bold">Why this matters</h2>
                <p className="mt-2.5 text-[14.5px] leading-relaxed text-slate-700">
                  {mod.why_it_matters}
                </p>
                <div className="mt-4 rounded-md bg-secondary p-3.5 text-[13.5px] text-slate-700">
                  <span className="font-semibold">When you use it: </span>
                  {mod.when_used}
                </div>
              </section>

              <section className="rounded-xl border border-border bg-[#0F172A] p-6 text-slate-100">
                <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Framework
                </div>
                <h2 className="mt-1.5 font-heading text-[20px] font-extrabold">
                  {mod.framework.name}
                </h2>
                <ol className="mt-5 space-y-0" data-testid="module-framework">
                  {mod.framework.steps.map((s, i) => (
                    <li key={s.label} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <span className="grid size-7 shrink-0 place-items-center rounded-full bg-sky-500/20 font-mono text-[12px] font-bold text-sky-300">
                          {i + 1}
                        </span>
                        {i < mod.framework.steps.length - 1 ? (
                          <span className="my-1 w-px flex-1 bg-slate-700" />
                        ) : null}
                      </div>
                      <div className="pb-5">
                        <div className="font-heading text-[15px] font-bold">{s.label}</div>
                        <p className="mt-0.5 text-[13.5px] leading-relaxed text-slate-300">
                          {s.detail}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>

              <section className="space-y-4" data-testid="module-examples">
                <h2 className="font-heading text-[19px] font-bold">Weak vs strong</h2>
                {mod.examples.map((ex, i) => (
                  <div
                    key={`${i}-${ex.weak.slice(0, 24)}`}
                    className="overflow-hidden rounded-xl border border-border bg-card"
                    data-testid={`module-example-${i}`}
                  >
                    <div className="grid md:grid-cols-2">
                      <div className="border-b border-border p-4 md:border-b-0 md:border-r">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-red-700">
                          <XCircle className="size-3.5" />
                          Weak
                        </div>
                        <p className="mt-2 text-[13.5px] leading-relaxed text-slate-700">
                          {ex.weak}
                        </p>
                      </div>
                      <div className="bg-emerald-50/50 p-4">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
                          <CheckCircle2 className="size-3.5" />
                          Strong
                        </div>
                        <p className="mt-2 text-[13.5px] leading-relaxed text-slate-800">
                          {ex.strong}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2.5 border-t border-border bg-secondary/60 p-4">
                      <Quote className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      <p className="text-[13px] leading-relaxed text-slate-700">
                        <span className="font-semibold">Why it's stronger: </span>
                        {ex.why}
                      </p>
                    </div>
                  </div>
                ))}
              </section>

              {mod.knowledge_check.length ? (
                <section className="rounded-xl border border-border bg-card p-6" data-testid="module-quiz">
                  <h2 className="font-heading text-[19px] font-bold">Quick check</h2>
                  <p className="text-[13px] text-muted-foreground">
                    Not graded — just confirm the concept landed.
                  </p>
                  <div className="mt-5 space-y-6">
                    {mod.knowledge_check.map((q, qi) => {
                      const picked = answers[qi];
                      return (
                        <div key={`${qi}-${q.question.slice(0, 32)}`} data-testid={`quiz-item-${qi}`}>
                          <div className="text-[14.5px] font-semibold">{q.question}</div>
                          <div className="mt-2.5 grid gap-2">
                            {q.options.map((opt, oi) => {
                              const chosen = picked === oi;
                              const correct = oi === q.answer;
                              const revealed = picked !== undefined;
                              return (
                                <button
                                  key={`${oi}-${opt.slice(0, 24)}`}
                                  type="button"
                                  onClick={() => setAnswers((a) => ({ ...a, [qi]: oi }))}
                                  data-testid={`quiz-${qi}-option-${oi}`}
                                  className={cn(
                                    "rounded-md border px-3.5 py-2.5 text-left text-[13.5px] transition-colors",
                                    revealed && correct
                                      ? "border-emerald-400 bg-emerald-50 text-emerald-900"
                                      : chosen
                                        ? "border-red-300 bg-red-50 text-red-900"
                                        : "border-border hover:border-slate-300",
                                  )}
                                >
                                  {opt}
                                </button>
                              );
                            })}
                          </div>
                          {picked !== undefined ? (
                            <p
                              className="mt-2.5 rounded-md bg-secondary p-3 text-[13px] leading-relaxed text-slate-700"
                              data-testid={`quiz-explanation-${qi}`}
                            >
                              {q.explanation}
                            </p>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </section>
              ) : null}
            </div>

            <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
              <section className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-heading text-[15px] font-bold">What you'll learn</h3>
                <ul className="mt-3 space-y-2" data-testid="module-objectives">
                  {mod.objectives.map((o) => (
                    <li key={o} className="flex gap-2 text-[13.5px] leading-snug">
                      <BadgeCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      {o}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-heading text-[15px] font-bold">Key terms</h3>
                <dl className="mt-3 space-y-3" data-testid="module-terms">
                  {mod.terms.map((t) => (
                    <div key={t.term}>
                      <dt className="text-[13.5px] font-semibold">{t.term}</dt>
                      <dd className="text-[12.5px] leading-snug text-muted-foreground">
                        {t.definition}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>

              <section className="rounded-xl border border-border bg-card p-5">
                <h3 className="flex items-center gap-2 font-heading text-[15px] font-bold">
                  <TriangleAlert className="size-4 text-amber-600" />
                  Beginner mistakes
                </h3>
                <ul className="mt-3 space-y-1.5" data-testid="module-mistakes">
                  {mod.mistakes.map((m) => (
                    <li key={m} className="text-[13px] leading-snug text-slate-700">
                      · {m}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
                <h3 className="font-heading text-[15px] font-bold text-emerald-900">
                  What strong looks like
                </h3>
                <ul className="mt-3 space-y-1.5" data-testid="module-strong">
                  {mod.strong_performance.map((m) => (
                    <li key={m} className="text-[13px] leading-snug text-emerald-900">
                      · {m}
                    </li>
                  ))}
                </ul>
                <p className="mt-3 border-t border-emerald-200 pt-3 text-[12px] text-emerald-800">
                  These are exactly the principles your scorecard grades after the call.
                </p>
              </section>
            </aside>
          </div>
        ) : null}

        {step === 1 ? (
          <div className="mt-7 grid gap-6 lg:grid-cols-2" data-testid="module-scenario">
            <section className="rounded-xl border border-border bg-card p-6">
              <SectionLabel icon={User} text="Your role" />
              <p className="mt-2 font-heading text-[17px] font-bold" data-testid="scenario-seller-role">
                {brief?.seller_role ?? "Sales representative"}
              </p>
              <p className="mt-1 text-[13.5px] text-muted-foreground">
                You are selling {brief?.product}.
              </p>

              {sheet ? (
                <div className="mt-6 space-y-5 border-t border-border pt-5" data-testid="product-sheet">
                  <div>
                    <SectionLabel icon={Info} text="What you sell" />
                    <p className="mt-2 font-heading text-[16px] font-bold">{sheet.name}</p>
                    <p className="text-[13.5px] leading-relaxed text-slate-700">{sheet.one_liner}</p>
                  </div>
                  <SheetList title="Primary features" items={sheet.features} testid="sheet-features" />
                  <SheetList title="Customer benefits" items={sheet.benefits} testid="sheet-benefits" />
                  <div>
                    <h4 className="text-[12.5px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      Pricing
                    </h4>
                    <p className="mt-1 text-[13.5px] leading-relaxed" data-testid="sheet-pricing">
                      {sheet.pricing}
                    </p>
                  </div>
                  <SheetList
                    title="Differentiators"
                    items={sheet.differentiators}
                    testid="sheet-differentiators"
                  />
                  <SheetList title="Limitations" items={sheet.limitations} testid="sheet-limitations" />
                  <SheetList title="Common use cases" items={sheet.use_cases} testid="sheet-use-cases" />
                </div>
              ) : null}
            </section>

            <div className="space-y-6">
              <section className="rounded-xl border border-border bg-card p-6">
                <SectionLabel icon={Building2} text="Who you're selling to" />
                <p className="mt-2 font-heading text-[17px] font-bold" data-testid="scenario-prospect">
                  {brief?.prospect_name}
                </p>
                <p className="text-[13.5px] text-muted-foreground">
                  {brief?.prospect_role} · {brief?.company}
                </p>
                <p className="mt-1 text-[13px] text-muted-foreground">
                  {brief?.company_size} · {brief?.industry}
                </p>
                <div className="mt-4 rounded-md bg-secondary p-3.5">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                    Known information
                  </div>
                  <p className="mt-1.5 text-[13.5px] leading-relaxed">{brief?.known}</p>
                </div>
                <p className="mt-3 text-[12.5px] leading-relaxed text-muted-foreground">
                  Everything else — the real problem, what it costs, budget, timeline, who decides —
                  is held by the prospect. You have to earn it with questions.
                </p>
              </section>

              <section className="rounded-xl border border-border bg-card p-6">
                <SectionLabel icon={Target} text="Your objective" />
                <p className="mt-2 text-[14.5px] leading-relaxed" data-testid="scenario-objective">
                  {brief?.objective}
                </p>
                <p className="mt-3 text-[12.5px] text-muted-foreground">
                  Not every call succeeds. At higher difficulty this prospect can decline, stall or
                  end the conversation — that is a real result, not a bug.
                </p>
              </section>

              <section className="rounded-xl border border-border bg-card p-6">
                <SectionLabel icon={ClipboardList} text="Skills being evaluated" />
                <div className="mt-3 flex flex-wrap gap-2" data-testid="scenario-skills">
                  {(mod?.focus_categories ?? exercise?.skills ?? []).map((s) => (
                    <Badge key={s} variant="secondary">
                      {s}
                    </Badge>
                  ))}
                </div>
                {mod ? (
                  <ul className="mt-4 space-y-1.5 border-t border-border pt-4">
                    {mod.graded_principles.map((p) => (
                      <li key={p} className="text-[13px] leading-snug text-slate-700">
                        · {p}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="mt-7 grid gap-6 lg:grid-cols-[1.1fr_1fr]" data-testid="module-prepare">
            <section className="rounded-xl border border-border bg-card p-6">
              <h2 className="font-heading text-[19px] font-bold">Pre-call prep sheet</h2>
              <dl className="mt-4 divide-y divide-border">
                {[
                  ["Your role", brief?.seller_role ?? "—"],
                  ["Company & product", sheet ? `${sheet.name} — ${sheet.one_liner}` : brief?.product ?? "—"],
                  [
                    "Prospect",
                    brief
                      ? `${brief.prospect_name}, ${brief.prospect_role} at ${brief.company} (${brief.company_size})`
                      : "—",
                  ],
                  ["Objective", brief?.objective ?? "—"],
                  ["Difficulty", `Level ${level} · ${difficulty?.name ?? ""}`],
                  ["Skills evaluated", (mod?.focus_categories ?? []).join(", ")],
                  ["Pricing you can quote", sheet?.pricing ?? "—"],
                ].map(([k, v]) => (
                  <div key={k as string} className="grid gap-1 py-3 sm:grid-cols-[150px_1fr]">
                    <dt className="text-[12px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      {k}
                    </dt>
                    <dd className="text-[13.5px] leading-relaxed">{v}</dd>
                  </div>
                ))}
              </dl>

              {brief?.things_to_remember?.length ? (
                <div className="mt-5 rounded-md bg-amber-50 p-4" data-testid="prepare-remember">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-800">
                    Things to remember
                  </div>
                  <ul className="mt-2 space-y-1.5">
                    {rememberList.map((t) => (
                      <li key={t} className="text-[13.5px] leading-snug text-amber-950">
                        · {t}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </section>

            <div className="space-y-6">
              <section className="rounded-xl border border-border bg-card p-6">
                <h3 className="font-heading text-[15px] font-bold">Set the resistance level</h3>
                <div className="mt-3 space-y-2" data-testid="prepare-difficulty">
                  {(difficulties ?? []).map((d) => (
                    <button
                      key={d.level}
                      type="button"
                      onClick={() => setLevel(d.level)}
                      data-testid={`prepare-difficulty-${d.level}`}
                      className={cn(
                        "flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors",
                        d.level === level
                          ? "border-primary bg-accent"
                          : "border-border hover:border-slate-300",
                      )}
                    >
                      <span
                        className={cn(
                          "grid size-7 shrink-0 place-items-center rounded-md font-heading text-[13px] font-bold",
                          d.level === level ? "bg-[#0F172A] text-white" : "bg-secondary",
                        )}
                      >
                        {d.level}
                      </span>
                      <span>
                        <span className="text-[13.5px] font-semibold">{d.name}</span>
                        <span className="ml-2 text-[12px] text-muted-foreground">{d.subtitle}</span>
                        <span className="mt-0.5 block text-[12.5px] leading-snug text-muted-foreground">
                          {d.behavior}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-border bg-[#0F172A] p-6 text-slate-100">
                <h3 className="font-heading text-[17px] font-bold">Ready when you are</h3>
                <p className="mt-2 text-[13.5px] text-slate-300">
                  You'll speak out loud; the prospect answers in voice. There is no coaching during
                  the call — the debrief comes after you hang up.
                </p>
                <Button
                  size="lg"
                  className="mt-5 w-full bg-white font-semibold text-[#0F172A] hover:bg-slate-200"
                  onClick={() => start.mutate()}
                  disabled={start.isPending || !brief}
                  data-testid="module-start-simulation"
                >
                  {start.isPending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Connecting…
                    </>
                  ) : (
                    <>
                      Start voice simulation
                      <ArrowRight className="size-4" />
                    </>
                  )}
                </Button>
                <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-800 pt-4 text-[12.5px]">
                  <button
                    type="button"
                    onClick={() => goto(0)}
                    className="text-slate-300 underline-offset-2 hover:underline"
                    data-testid="prepare-review-training"
                  >
                    Review the training
                  </button>
                  {scenarios && scenarios.length > 1 ? (
                    <button
                      type="button"
                      onClick={() => setScenarioIdx((i) => i + 1)}
                      className="text-slate-300 underline-offset-2 hover:underline"
                      data-testid="prepare-new-scenario"
                    >
                      Different scenario
                    </button>
                  ) : null}
                </div>
              </section>
            </div>
          </div>
        ) : null}

        <div className="mt-8 flex items-center justify-between border-t border-border pt-6">
          <Button
            variant="ghost"
            onClick={() => goto(Math.max(0, step - 1))}
            disabled={step === 0}
            data-testid="module-prev"
          >
            <ArrowLeft className="size-4" />
            Back
          </Button>
          {step < 2 ? (
            <Button onClick={() => goto(step + 1)} data-testid="module-next" className="font-semibold">
              {step === 0 ? "See the scenario" : "Prepare for the call"}
              <ArrowRight className="size-4" />
            </Button>
          ) : (
            <Link
              to="/training"
              className={cn(buttonVariants({ variant: "ghost" }))}
              data-testid="module-other-skills"
            >
              Other skills
            </Link>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function SectionLabel({
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

function SheetList({
  title,
  items,
  testid,
}: {
  title: string;
  items: string[];
  testid: string;
}) {
  if (!items.length) return null;
  return (
    <div data-testid={testid}>
      <h4 className="text-[12.5px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
        {title}
      </h4>
      <ul className="mt-1.5 space-y-1">
        {items.map((i) => (
          <li key={i} className="text-[13.5px] leading-snug text-slate-700">
            · {i}
          </li>
        ))}
      </ul>
    </div>
  );
}
