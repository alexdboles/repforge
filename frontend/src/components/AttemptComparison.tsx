import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, TrendingDown, TrendingUp } from "lucide-react";
import { apiGet } from "@/lib/api";
import { scoreTone } from "@/lib/profile";
import type { Attempt, AttemptSeries } from "@/lib/types";
import { cn } from "@/lib/utils";

/** "vs your previous attempts" — the proof that repetition is working. */
export default function AttemptComparison({
  userId,
  exerciseId,
  currentSimId,
  compact = false,
}: {
  userId: string;
  exerciseId: string;
  currentSimId?: string;
  compact?: boolean;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["attempts", userId, exerciseId],
    queryFn: () => apiGet<AttemptSeries>(`/users/${userId}/attempts/${exerciseId}`),
    enabled: Boolean(userId && exerciseId),
    retry: false,
  });

  if (isLoading) {
    return <div className="h-24 animate-pulse rounded-lg bg-secondary" data-testid="attempts-loading" />;
  }
  if (!data) return null;

  const attempts = data.attempts;
  if (attempts.length < 2) {
    return (
      <div
        className="rounded-xl border border-dashed border-border bg-card p-5 text-[13px] text-muted-foreground"
        data-testid="attempts-need-more"
      >
        Run {data.exercise_name} once more and this panel compares the attempts side by side —
        overall score, every competency and what changed.
      </div>
    );
  }

  const deltas = Object.entries(data.category_deltas).sort((a, b) => b[1] - a[1]);
  const chart = attempts.map((a) => ({
    label: `#${a.index}`,
    score: a.overall_score,
    difficulty: a.difficulty,
  }));

  return (
    <div className="rounded-xl border border-border bg-card p-5" data-testid="attempt-comparison">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-heading text-[17px] font-bold">
            {data.exercise_name} · attempt {attempts.length}
          </h3>
          <p className="text-[12.5px] text-muted-foreground">
            First attempt {data.first_score} → latest {data.latest_score} · best {data.best_score}
          </p>
        </div>
        <span
          className={cn(
            "flex items-center gap-1.5 rounded-full px-3 py-1 text-[13px] font-bold",
            data.delta >= 0 ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800",
          )}
          data-testid="attempt-delta"
        >
          {data.delta >= 0 ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />}
          {data.delta > 0 ? "+" : ""}
          {data.delta} pts
        </span>
      </div>

      <div className="mt-4 h-[150px]" data-testid="attempt-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart} margin={{ left: -24, right: 6, top: 6 }}>
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748B" }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748B" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
            <Line type="monotone" dataKey="score" stroke="#2563EB" strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 grid gap-3 sm:grid-cols-2">
        {data.most_improved ? (
          <div className="rounded-md bg-emerald-50 p-3" data-testid="most-improved">
            <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-700">
              Most improved
            </div>
            <div className="mt-1 text-[14px] font-bold text-emerald-900">
              {data.most_improved} {data.category_deltas[data.most_improved] > 0 ? "+" : ""}
              {data.category_deltas[data.most_improved]}
            </div>
          </div>
        ) : null}
        {data.still_weakest ? (
          <div className="rounded-md bg-amber-50 p-3" data-testid="still-weakest">
            <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-800">
              Still weakest
            </div>
            <div className="mt-1 text-[14px] font-bold text-amber-900">{data.still_weakest}</div>
          </div>
        ) : null}
      </div>

      {!compact && deltas.length ? (
        <CategoryDeltas deltas={deltas} first={attempts[0]} latest={attempts[attempts.length - 1]} />
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-4">
        {attempts.map((a) => (
          <Link
            key={a.simulation_id}
            to={`/scorecard/${a.simulation_id}`}
            data-testid={`attempt-link-${a.index}`}
            className={cn(
              "rounded-md border px-2.5 py-1.5 text-[12px] font-semibold",
              a.simulation_id === currentSimId
                ? "border-primary bg-accent"
                : "border-border hover:border-slate-300",
            )}
          >
            #{a.index} · L{a.difficulty} · {a.overall_score}
          </Link>
        ))}
      </div>
    </div>
  );
}

/** First-attempt vs latest movement, one row per competency. */
function CategoryDeltas({
  deltas,
  first,
  latest,
}: {
  deltas: [string, number][];
  first: Attempt;
  latest: Attempt;
}) {
  return (
  <div className="mt-4 border-t border-border pt-4" data-testid="attempt-category-deltas">
    <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
      First attempt vs latest, by competency
    </div>
    <div className="mt-2 divide-y divide-border">
      {deltas.map(([cat, delta]) => (
        <div
          key={cat}
          className="flex items-center justify-between py-2 text-[13.5px]"
          data-testid={`delta-${cat.toLowerCase().replace(/\s+/g, "-")}`}
        >
          <span>{cat}</span>
          <span className="flex items-center gap-3 font-mono">
            <span className="text-muted-foreground">{first.categories[cat]}</span>
            <ArrowRight className="size-3 text-muted-foreground" />
            <span className={scoreTone(latest.categories[cat])}>
              {latest.categories[cat]}
            </span>
            <span
              className={cn(
                "w-10 text-right font-semibold",
                delta >= 0 ? "text-emerald-600" : "text-red-600",
              )}
            >
              {delta > 0 ? "+" : ""}
              {delta}
            </span>
          </span>
        </div>
      ))}
    </div>
  </div>
  );
}
