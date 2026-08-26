import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Mic, BarChart3, Sparkles, ShieldCheck, Clock, Users } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";
import { getUserId, setUserId } from "@/lib/profile";
import type { Exercise, UserProfile } from "@/lib/types";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    icon: ShieldCheck,
    title: "Pick the situation",
    body: "Eight exercise types, five difficulty tiers, and scenarios with information deliberately hidden from you.",
  },
  {
    icon: Mic,
    title: "Talk to the prospect",
    body: "Speak out loud. The AI buyer pushes back, objects, withholds detail, and never breaks character to coach you.",
  },
  {
    icon: BarChart3,
    title: "Get graded, then repeat",
    body: "A scored breakdown across 14 selling competencies, quoted from your actual words, plus what to practice next.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const existing = getUserId();
  const { data: exercises } = useQuery({
    queryKey: ["exercises"],
    queryFn: () => apiGet<Exercise[]>("/exercises"),
    retry: false,
  });

  const create = useMutation({
    mutationFn: (payload: { name: string }) => apiPost<UserProfile>("/users", payload),
    onSuccess: (user) => {
      setUserId(user.id);
      navigate("/learn/cold-call?difficulty=2");
    },
    onError: () => toast.error("Could not create your profile. Please try again."),
  });

  const start = () => create.mutate({ name: name.trim() || "Demo Rep" });

  return (
    <div className="min-h-screen bg-background" data-testid="landing-page">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-5 sm:px-8">
          <div className="flex items-center gap-2.5">
            <span className="grid size-8 place-items-center rounded-md bg-[#0F172A] text-white">
              <Mic className="size-4" />
            </span>
            <span className="font-heading text-[17px] font-extrabold tracking-tight">VocalPitch</span>
          </div>
          {existing ? (
            <Link
              to="/dashboard"
              data-testid="landing-goto-dashboard"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Go to dashboard
            </Link>
          ) : (
            <span className="text-[13px] text-muted-foreground">Practice. Perform. Improve.</span>
          )}
        </div>
      </header>

      <section className="mx-auto grid max-w-[1200px] gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
        <div className="animate-rise">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-[12px] font-semibold text-slate-600">
            <Sparkles className="size-3.5 text-primary" />
            AI sales flight simulator
          </span>
          <h1 className="mt-6 font-heading text-[40px] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[56px]">
            Practice the conversation
            <br />
            before it counts.
          </h1>
          <p className="mt-6 max-w-xl text-[16.5px] leading-relaxed text-muted-foreground">
            First we teach the skill. Then you practise it out loud against an AI prospect who
            withholds information, objects and can walk away. Then you get coaching quoted from your
            own words — and you can run the whole loop against your real product, not just ours.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            {existing ? (
              <Link
                to="/learn/cold-call?difficulty=2"
                data-testid="landing-start-existing"
                className={cn(buttonVariants({ size: "lg" }), "font-semibold")}
              >
                Start a simulation
                <ArrowRight className="size-4" />
              </Link>
            ) : (
              <>
                <Input
                  data-testid="landing-name-input"
                  placeholder="Your name (optional)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="h-11 sm:max-w-[240px]"
                />
                <Button
                  size="lg"
                  onClick={start}
                  disabled={create.isPending}
                  data-testid="landing-start-first-simulation"
                  className="font-semibold"
                >
                  {create.isPending ? "Preparing your cockpit…" : "Start Your First Simulation"}
                  <ArrowRight className="size-4" />
                </Button>
              </>
            )}
          </div>
          <p className="mt-3 text-[12.5px] text-muted-foreground">
            No setup. A pre-configured cold-call scenario is ready — you'll be talking to a prospect
            in under a minute.
          </p>

          <dl className="mt-12 grid grid-cols-3 gap-6 border-t border-border pt-8">
            {[
              { k: "8", v: "exercise types" },
              { k: "5", v: "difficulty tiers" },
              { k: "14", v: "graded competencies" },
            ].map((s) => (
              <div key={s.v}>
                <dt className="font-heading text-[28px] font-extrabold leading-none">{s.k}</dt>
                <dd className="mt-1 text-[12.5px] text-muted-foreground">{s.v}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="animate-rise">
          <div className="overflow-hidden rounded-xl border border-[#1E293B] bg-[#090D16] p-6 text-slate-100 shadow-[0_18px_50px_rgba(15,23,42,0.18)]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                <span className="size-2 animate-pulse rounded-full bg-red-500" />
                Live simulation
              </span>
              <span className="font-mono text-[13px] text-slate-300">03:42</span>
            </div>
            <div className="mt-6 flex items-center gap-4">
              <div className="grid size-12 place-items-center rounded-full bg-slate-800 font-heading text-[15px] font-bold">
                JM
              </div>
              <div>
                <div className="font-heading text-[16px] font-bold">Jordan Miller</div>
                <div className="text-[12.5px] text-slate-400">VP of Sales · Harborline Logistics</div>
              </div>
            </div>
            <div className="mt-6 flex h-16 items-end gap-1.5">
              {[0.3, 0.7, 0.45, 0.95, 0.6, 0.85, 0.4, 0.7, 0.5, 0.9, 0.35, 0.65, 0.8, 0.45, 0.7].map(
                (h, i) => (
                  <span
                    key={i}
                    className="flex-1 origin-bottom rounded-sm bg-sky-400/80 animate-wave"
                    style={{ height: `${h * 100}%`, animationDelay: `${i * 70}ms` }}
                  />
                ),
              )}
            </div>
            <div className="mt-6 space-y-3 text-[13.5px]">
              <p className="rounded-md bg-slate-800/70 p-3 text-slate-200">
                “Look, we already have a system for this. What exactly are you calling about?”
              </p>
              <p className="rounded-md border border-slate-700 p-3 text-slate-400">
                You: “Fair enough — can I ask what made you take my call?”
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            {[
              { icon: Clock, label: "Unlimited reps" },
              { icon: BarChart3, label: "Measured skills" },
              { icon: Users, label: "Team ready" },
            ].map((f) => (
              <div
                key={f.label}
                className="rounded-lg border border-border bg-card p-3 text-[12px] font-medium"
              >
                <f.icon className="mb-2 size-4 text-primary" />
                {f.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-border bg-card">
        <div className="mx-auto grid max-w-[1200px] gap-8 px-5 py-14 sm:px-8 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <div key={s.title}>
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-md bg-secondary">
                  <s.icon className="size-4 text-primary" />
                </span>
                <span className="font-mono text-[12px] text-muted-foreground">
                  0{i + 1}
                </span>
              </div>
              <h3 className="mt-4 font-heading text-[18px] font-bold">{s.title}</h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-muted-foreground">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-[1200px] px-5 py-14 sm:px-8">
        <h2 className="font-heading text-[24px] font-extrabold">The training library</h2>
        <p className="mt-2 text-[14px] text-muted-foreground">
          Every exercise runs live, in voice, with a scored debrief afterwards.
        </p>
        <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(exercises ?? []).map((ex) => (
            <div
              key={ex.id}
              className="rounded-lg border border-border bg-card p-4"
              data-testid={`landing-exercise-${ex.id}`}
            >
              <div className="font-heading text-[15px] font-bold">{ex.name}</div>
              <p className="mt-1.5 text-[12.5px] leading-snug text-muted-foreground">{ex.tagline}</p>
            </div>
          ))}
          {!exercises
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg bg-secondary" />
              ))
            : null}
        </div>
      </section>
    </div>
  );
}
