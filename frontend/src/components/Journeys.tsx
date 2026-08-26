import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Check, Loader2, UserRound } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { getUserId, scoreTone } from "@/lib/profile";
import type { Exercise, JourneyView, Simulation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Recurring characters: the same prospect across several exercises, with memory. */
export default function Journeys({ difficulty = 2 }: { difficulty?: number }) {
  const userId = getUserId();
  const navigate = useNavigate();
  const { data: journeys, isLoading } = useQuery({
    queryKey: ["journeys", userId],
    queryFn: () => apiGet<JourneyView[]>(`/users/${userId}/journeys`),
    enabled: Boolean(userId),
    retry: false,
  });
  const { data: exercises } = useQuery({
    queryKey: ["exercises"],
    queryFn: () => apiGet<Exercise[]>("/exercises"),
    retry: false,
  });

  const start = useMutation({
    mutationFn: (vars: { journeyId: string; exerciseId: string }) =>
      apiPost<Simulation>("/simulations", {
        user_id: userId,
        exercise_id: vars.exerciseId,
        difficulty,
        journey_id: vars.journeyId,
        mode: "journey",
      }),
    onSuccess: (sim) => navigate(`/simulation/${sim.id}`),
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not start this stage.";
      toast.error(detail);
    },
  });

  const nameOf = (id: string) => exercises?.find((e) => e.id === id)?.name ?? id;

  if (isLoading) {
    return <div className="h-40 animate-pulse rounded-xl bg-secondary" data-testid="journeys-loading" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3" data-testid="journeys-list">
      {(journeys ?? []).map((j) => {
        const pct = Math.round((j.completed_stages / j.stages.length) * 100);
        return (
          <div
            key={j.id}
            className="flex flex-col rounded-xl border border-border bg-card p-5"
            data-testid={`journey-card-${j.id}`}
          >
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-full bg-[#0F172A] text-white">
                <UserRound className="size-4" />
              </span>
              <div className="min-w-0">
                <div className="font-heading text-[16px] font-bold">{j.character}</div>
                <div className="text-[12.5px] text-muted-foreground">
                  {j.role} · {j.company}
                </div>
              </div>
              <span className="ml-auto font-mono text-[12px] text-muted-foreground">
                {j.completed_stages}/{j.stages.length}
              </span>
            </div>

            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">{j.blurb}</p>

            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${pct}%`, transition: "width 600ms ease-out" }}
              />
            </div>

            <ol className="mt-4 flex-1 space-y-1.5">
              {j.stages.map((s, i) => (
                <li
                  key={s.exercise_id}
                  className="flex items-center gap-2 text-[13px]"
                  data-testid={`journey-stage-${j.id}-${s.exercise_id}`}
                >
                  <span
                    className={cn(
                      "grid size-5 shrink-0 place-items-center rounded-full text-[10px] font-bold",
                      s.completed ? "bg-emerald-100 text-emerald-800" : "bg-secondary text-slate-500",
                    )}
                  >
                    {s.completed ? <Check className="size-3" /> : i + 1}
                  </span>
                  <span className={cn("min-w-0 flex-1 truncate", s.completed && "text-muted-foreground")}>
                    {nameOf(s.exercise_id)}
                  </span>
                  {s.best_score !== null ? (
                    <span className={cn("font-mono text-[12px] font-semibold", scoreTone(s.best_score))}>
                      {s.best_score}
                    </span>
                  ) : null}
                </li>
              ))}
            </ol>

            <Button
              className="mt-4 w-full font-semibold"
              variant={j.next_exercise_id ? "default" : "outline"}
              disabled={start.isPending}
              onClick={() =>
                start.mutate({
                  journeyId: j.id,
                  exerciseId: j.next_exercise_id ?? j.stages[0].exercise_id,
                })
              }
              data-testid={`journey-start-${j.id}`}
            >
              {start.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <>
                  {j.next_exercise_id
                    ? `Continue: ${nameOf(j.next_exercise_id)}`
                    : `Replay ${nameOf(j.stages[0].exercise_id)}`}
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
