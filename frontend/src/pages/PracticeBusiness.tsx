import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Briefcase,
  Building2,
  Info,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
  Trash2,
  User,
} from "lucide-react";
import { toast } from "sonner";
import { apiDelete, apiGet, apiPost, ApiError } from "@/lib/api";
import { getUserId } from "@/lib/profile";
import type {
  CustomScenario,
  Difficulty,
  Exercise,
  SalesProfile,
  Simulation,
} from "@/lib/types";
import AppShell from "@/components/AppShell";
import { EmptyState } from "@/components/Metrics";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export default function PracticeBusiness() {
  const userId = getUserId();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [exerciseId, setExerciseId] = useState("cold-call");
  const [level, setLevel] = useState(3);
  const [preferences, setPreferences] = useState("");
  const [scenario, setScenario] = useState<CustomScenario | null>(null);

  const { data: profiles, isLoading } = useQuery({
    queryKey: ["sales-profiles", userId],
    queryFn: () => apiGet<SalesProfile[]>(`/users/${userId}/sales-profiles`),
    enabled: Boolean(userId),
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

  const selectedId = params.get("profile") ?? profiles?.[0]?.id ?? "";
  const profile = profiles?.find((p) => p.id === selectedId) ?? profiles?.[0];

  const generate = useMutation({
    mutationFn: () =>
      apiPost<CustomScenario>("/custom-scenarios", {
        profile_id: profile?.id,
        exercise_id: exerciseId,
        difficulty: level,
        preferences,
      }),
    onSuccess: (s) => setScenario(s),
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Scenario generation failed. Try again.";
      toast.error(detail);
    },
  });

  const start = useMutation({
    mutationFn: () =>
      apiPost<Simulation>("/simulations", {
        user_id: userId,
        exercise_id: exerciseId,
        difficulty: level,
        custom_scenario_id: scenario?.id,
        mode: "business",
      }),
    onSuccess: (sim) => navigate(`/simulation/${sim.id}`),
    onError: () => toast.error("Could not start the simulation."),
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiDelete<{ deleted: boolean }>(`/sales-profiles/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-profiles", userId] });
      setScenario(null);
      toast.success("Profile deleted");
    },
  });

  if (!userId) return <Navigate to="/" replace />;

  const exercise = exercises?.find((e) => e.id === exerciseId);

  return (
    <AppShell>
      <div data-testid="practice-business-page">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Badge variant="secondary">
              <Briefcase className="size-3" />
              Practice My Business
            </Badge>
            <h1 className="mt-2 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              Rehearse your actual sales job
            </h1>
            <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
              Save your company, product, buyers, pricing, competitors and the objections you really
              hear. We generate a fresh prospect from it every time — so you can practise tomorrow's
              call today.
            </p>
          </div>
          <Link
            to="/practice-business/setup"
            className={cn(buttonVariants(), "font-semibold")}
            data-testid="new-sales-profile"
          >
            <Plus className="size-4" />
            New sales profile
          </Link>
        </div>

        {isLoading ? (
          <div className="mt-8 h-28 animate-pulse rounded-lg bg-secondary" data-testid="pmb-loading" />
        ) : null}

        {profiles && !profiles.length ? (
          <div className="mt-8">
            <EmptyState
              testid="pmb-empty"
              title="No sales profile yet"
              body="Answer seven short steps about your company, product and buyers. It takes about two minutes and you only do it once — after that, launching a custom simulation takes under a minute."
              action={
                <Link
                  to="/practice-business/setup"
                  className={cn(buttonVariants(), "font-semibold")}
                  data-testid="pmb-empty-cta"
                >
                  Set up my business
                  <ArrowRight className="size-4" />
                </Link>
              }
            />
          </div>
        ) : null}

        {profiles && profiles.length ? (
          <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
            <div className="space-y-6">
              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  1 · Choose sales profile
                </h2>
                <div className="mt-3 space-y-2" data-testid="profile-list">
                  {profiles.map((p) => (
                    <div
                      key={p.id}
                      className={cn(
                        "flex items-start gap-3 rounded-lg border p-3.5 transition-colors",
                        p.id === profile?.id
                          ? "border-primary bg-accent"
                          : "border-border hover:border-slate-300",
                      )}
                      data-testid={`profile-card-${p.id}`}
                    >
                      <button
                        type="button"
                        className="min-w-0 flex-1 text-left"
                        onClick={() => {
                          setParams({ profile: p.id }, { replace: true });
                          setScenario(null);
                        }}
                        data-testid={`select-profile-${p.id}`}
                      >
                        <div className="truncate font-heading text-[15px] font-bold">{p.label}</div>
                        <div className="truncate text-[12.5px] text-muted-foreground">
                          {p.company} · {p.product}
                        </div>
                        <div className="mt-1 text-[12px] text-muted-foreground">
                          Sells to {p.customer_type.toLowerCase()} · goal: {p.call_goal.toLowerCase()}
                        </div>
                      </button>
                      <Link
                        to={`/practice-business/setup/${p.id}`}
                        className="text-muted-foreground hover:text-foreground"
                        aria-label="Edit profile"
                        data-testid={`edit-profile-${p.id}`}
                      >
                        <Pencil className="size-3.5" />
                      </Link>
                      <button
                        type="button"
                        onClick={() => remove.mutate(p.id)}
                        className="text-muted-foreground hover:text-destructive"
                        aria-label="Delete profile"
                        data-testid={`delete-profile-${p.id}`}
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  2 · Choose skill
                </h2>
                <div className="mt-3 grid gap-2 sm:grid-cols-2" data-testid="pmb-exercises">
                  {(exercises ?? []).map((ex) => (
                    <button
                      key={ex.id}
                      type="button"
                      onClick={() => {
                        setExerciseId(ex.id);
                        setScenario(null);
                      }}
                      data-testid={`pmb-exercise-${ex.id}`}
                      className={cn(
                        "rounded-lg border p-3 text-left text-[13.5px] font-semibold transition-colors",
                        ex.id === exerciseId
                          ? "border-primary bg-accent"
                          : "border-border hover:border-slate-300",
                      )}
                    >
                      {ex.name}
                    </button>
                  ))}
                </div>

                <h2 className="mt-6 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  3 · Choose difficulty
                </h2>
                <div className="mt-3 flex flex-wrap gap-2" data-testid="pmb-difficulties">
                  {(difficulties ?? []).map((d) => (
                    <button
                      key={d.level}
                      type="button"
                      onClick={() => {
                        setLevel(d.level);
                        setScenario(null);
                      }}
                      data-testid={`pmb-difficulty-${d.level}`}
                      className={cn(
                        "rounded-lg border px-3.5 py-2 text-[13px] font-semibold transition-colors",
                        d.level === level
                          ? "border-primary bg-accent"
                          : "border-border hover:border-slate-300",
                      )}
                    >
                      L{d.level} · {d.name}
                    </button>
                  ))}
                </div>

                <h2 className="mt-6 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  4 · Scenario preferences (optional)
                </h2>
                <Input
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  placeholder="e.g. they're already using Competitor X and the CFO is involved"
                  className="mt-3"
                  data-testid="pmb-preferences"
                />

                <Button
                  size="lg"
                  className="mt-5 w-full font-semibold"
                  onClick={() => generate.mutate()}
                  disabled={generate.isPending || !profile}
                  data-testid="generate-scenario-button"
                >
                  {generate.isPending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Generating a prospect…
                    </>
                  ) : (
                    <>
                      <Sparkles className="size-4" />
                      {scenario ? "Generate new scenario" : "Generate scenario"}
                    </>
                  )}
                </Button>
              </section>
            </div>

            <section className="lg:sticky lg:top-24 lg:self-start">
              <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                5 · Review brief & start
              </h2>
              {!scenario ? (
                <div
                  className="mt-3 rounded-xl border border-dashed border-border bg-card px-6 py-14 text-center"
                  data-testid="scenario-placeholder"
                >
                  <Sparkles className="mx-auto size-5 text-muted-foreground" />
                  <h3 className="mt-3 font-heading text-[16px] font-bold">No scenario yet</h3>
                  <p className="mx-auto mt-2 max-w-sm text-[13px] text-muted-foreground">
                    Generate one and we'll invent a specific buyer for {profile?.product ?? "your product"} —
                    with a hidden problem, budget reality and objections you'll have to uncover.
                  </p>
                </div>
              ) : (
                <div
                  className="mt-3 overflow-hidden rounded-xl border border-border bg-card"
                  data-testid="custom-scenario-brief"
                >
                  <div className="bg-[#0F172A] p-5 text-slate-100">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                        {exercise?.name} · your business
                      </span>
                      <span className="rounded-full bg-slate-800 px-2.5 py-1 text-[11px] font-semibold">
                        Level {scenario.difficulty}
                      </span>
                    </div>
                    <h3 className="mt-3 font-heading text-[19px] font-extrabold">
                      {scenario.seller_role}
                    </h3>
                    <p className="text-[13px] text-slate-400">Selling {scenario.product}</p>
                  </div>

                  <div className="divide-y divide-border">
                    <div className="p-5">
                      <Label2 icon={User} text="Prospect" />
                      <p className="mt-2 font-heading text-[16px] font-bold" data-testid="custom-prospect-name">
                        {scenario.prospect_name}
                      </p>
                      <p className="text-[13px] text-muted-foreground">
                        {scenario.prospect_role} · {scenario.company}
                      </p>
                      <p className="mt-1 flex items-center gap-1.5 text-[12.5px] text-muted-foreground">
                        <Building2 className="size-3.5" />
                        {scenario.company_size} · {scenario.industry}
                      </p>
                      <p className="mt-2 text-[12.5px] text-muted-foreground">Mood: {scenario.mood}</p>
                    </div>
                    <div className="p-5">
                      <Label2 icon={Info} text="What you know going in" />
                      <p className="mt-2 text-[13.5px] leading-relaxed" data-testid="custom-known">
                        {scenario.known}
                      </p>
                    </div>
                    <div className="p-5">
                      <Label2 icon={Target} text="Objective" />
                      <p className="mt-2 text-[13.5px] leading-relaxed">{scenario.objective}</p>
                    </div>
                    <div className="bg-secondary/60 p-5 text-[12.5px] leading-relaxed text-muted-foreground">
                      This prospect is holding a hidden problem, a budget reality and a reason to
                      resist change. None of it is shown here — earn it in the conversation.
                    </div>
                  </div>

                  <div className="space-y-2 border-t border-border p-5">
                    <Button
                      size="lg"
                      className="w-full font-semibold"
                      onClick={() => start.mutate()}
                      disabled={start.isPending}
                      data-testid="pmb-start-simulation"
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
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => generate.mutate()}
                      disabled={generate.isPending}
                      data-testid="pmb-regenerate"
                    >
                      <RefreshCw className="size-4" />
                      Different prospect, same skill
                    </Button>
                  </div>
                </div>
              )}
            </section>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function Label2({
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
