import { CheckCircle2, Loader2, RotateCcw, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Miss, Strength } from "@/lib/types";

/** "What you did well" — quoted, conversation-specific praise. */
export function StrengthsSection({ strengths }: { strengths: Strength[] }) {
  return (
  <section className="rounded-xl border border-border bg-card p-5">
    <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
      <CheckCircle2 className="size-4 text-emerald-600" />
      What you did well
    </h2>
    <div className="mt-4 space-y-3" data-testid="strengths-list">
      {strengths.map((s, i) => (
        <div
          key={`${i}-${s.title}`}
          className="rounded-md border-l-4 border-emerald-500 bg-emerald-50/70 p-3.5"
          data-testid={`strength-${i}`}
        >
          <div className="font-heading text-[14.5px] font-bold text-emerald-900">
            {s.title}
          </div>
          <p className="mt-1 text-[13px] leading-relaxed text-emerald-950/80">
            {s.detail}
          </p>
          {s.quote ? (
            <p className="mt-2 font-mono text-[12px] italic text-emerald-800">
              “{s.quote}”
            </p>
          ) : null}
        </div>
      ))}
      {!strengths.length ? (
        <p className="text-[13px] text-muted-foreground">
          Nothing stood out as a strength on this call — the coaching below is where to
          start.
        </p>
      ) : null}
    </div>
  </section>
  );
}

/** "Missed opportunities" — each one is a practisable moment, so every card
 * offers Retry That Moment rather than just a critique. */
export function MissesSection({
  misses,
  onRetry,
  retrying,
}: {
  misses: Miss[];
  onRetry: (index: number) => void;
  retrying: boolean;
}) {
  return (
  <section className="rounded-xl border border-border bg-card p-5">
    <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
      <TriangleAlert className="size-4 text-amber-600" />
      Missed opportunities
    </h2>
    <div className="mt-4 space-y-3" data-testid="misses-list">
      {misses.map((s, i) => (
        <div
          key={`${i}-${s.title}`}
          className="rounded-md border-l-4 border-amber-500 bg-amber-50/70 p-3.5"
          data-testid={`miss-${i}`}
        >
          <div className="font-heading text-[14.5px] font-bold text-amber-900">
            {s.title}
          </div>
          <p className="mt-1 text-[13px] leading-relaxed text-amber-950/80">
            {s.detail}
          </p>
          {s.quote ? (
            <p className="mt-2 font-mono text-[12px] italic text-amber-800">
              “{s.quote}”
            </p>
          ) : null}
          {s.better_approach ? (
            <div className="mt-2.5 rounded-md bg-white p-2.5 text-[13px]">
              <span className="font-semibold text-slate-900">Better approach: </span>
              <span className="text-slate-700">{s.better_approach}</span>
            </div>
          ) : null}
          <Button
            size="sm"
            className="mt-3 font-semibold"
            onClick={() => onRetry(i)}
            disabled={retrying}
            data-testid={`retry-moment-${i}`}
          >
            {retrying ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <RotateCcw className="size-3.5" />
            )}
            Retry that moment
          </Button>
        </div>
      ))}
    </div>
  </section>
  );
}
