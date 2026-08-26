import { cn } from "@/lib/utils";
import { scoreBar, scoreTone } from "@/lib/profile";

export function ScoreRing({
  score,
  size = 168,
  label = "Overall",
  testid = "score-ring",
}: {
  score: number;
  size?: number;
  label?: string;
  testid?: string;
}) {
  const r = size / 2 - 10;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const stroke = score >= 80 ? "#16A34A" : score >= 60 ? "#D97706" : "#DC2626";
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E2E8F0" strokeWidth="10" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
          style={{ transition: "stroke-dashoffset 900ms ease-out" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="font-heading text-[38px] font-extrabold leading-none" data-testid={testid}>
          {score}
        </div>
        <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
          {label}
        </div>
      </div>
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  testid,
  tone,
}: {
  label: string;
  value: string;
  hint?: string;
  testid: string;
  tone?: string;
}) {
  return (
    <div
      className="rounded-lg border border-border bg-card p-4 transition-shadow hover:shadow-sm"
      data-testid={testid}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </div>
      <div className={cn("mt-2 font-heading text-[27px] font-extrabold leading-none", tone)}>
        {value}
      </div>
      {hint ? <div className="mt-1.5 text-[12px] text-muted-foreground">{hint}</div> : null}
    </div>
  );
}

export function SkillBar({
  category,
  score,
  note,
  attempts,
  testid,
}: {
  category: string;
  score: number;
  note?: string;
  attempts?: number;
  testid?: string;
}) {
  return (
    <div data-testid={testid} className="py-2.5">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[14px] font-medium">{category}</span>
        <span className={cn("font-mono text-[13px] font-semibold", scoreTone(score))}>
          {score}
          {attempts ? (
            <span className="ml-1.5 text-[11px] font-normal text-muted-foreground">
              · {attempts}x
            </span>
          ) : null}
        </span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-secondary">
        <div
          className={cn("h-full rounded-full", scoreBar(score))}
          style={{ width: `${score}%`, transition: "width 800ms ease-out" }}
        />
      </div>
      {note ? <p className="mt-1.5 text-[12.5px] leading-snug text-muted-foreground">{note}</p> : null}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
  testid,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
  testid: string;
}) {
  return (
    <div
      className="rounded-lg border border-dashed border-border bg-card px-6 py-12 text-center"
      data-testid={testid}
    >
      <h3 className="font-heading text-[17px] font-bold">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-[13.5px] text-muted-foreground">{body}</p>
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </div>
  );
}

export function DifficultyPips({ level }: { level: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`Level ${level}`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={cn(
            "h-2.5 w-1 rounded-sm",
            i <= level ? "bg-[#0F172A]" : "bg-slate-200",
          )}
        />
      ))}
    </span>
  );
}
