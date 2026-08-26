import { cn } from "@/lib/utils";

/** Speaking/listening indicator. Presentational only — extracted from the
 * simulation cockpit so that screen stays about conversation state. */
export default function WaveBars({
  active,
  tone,
  bars = 28,
}: {
  active: boolean;
  tone: "prospect" | "rep" | "idle";
  bars?: number;
}) {
  return (
    <div className="flex h-14 items-end justify-center gap-1 px-6 pb-2" data-testid="wave-bars">
      {Array.from({ length: bars }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "flex-1 origin-bottom rounded-sm transition-colors",
            tone === "prospect"
              ? "bg-sky-400/80"
              : tone === "rep"
                ? "bg-emerald-400/70"
                : "bg-slate-800",
          )}
          style={{
            height: `${20 + ((i * 37) % 70)}%`,
            animation: active ? `wave ${0.8 + (i % 5) * 0.12}s ease-in-out ${i * 40}ms infinite` : undefined,
            transform: active ? undefined : "scaleY(0.2)",
          }}
        />
      ))}
    </div>
  );
}
