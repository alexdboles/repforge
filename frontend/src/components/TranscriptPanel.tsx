import type { RefObject } from "react";
import { cn } from "@/lib/utils";
import type { TranscriptTurn } from "@/lib/types";

/** Live conversation view: the frozen-at-end transcript plus the two provisional
 * lines (the reply being sent, and the interim speech recognition text).
 * Presentational only — extracted from the simulation cockpit. */
export default function TranscriptPanel({
  turns,
  prospectName,
  pendingRep,
  interim,
  scrollRef,
}: {
  turns: TranscriptTurn[];
  prospectName: string;
  pendingRep: string | null;
  interim: string;
  scrollRef: RefObject<HTMLDivElement | null>;
}) {
  return (
    <div
      ref={scrollRef}
      className="max-h-[42vh] min-h-[220px] flex-1 space-y-3 overflow-y-auto px-5 py-4"
      data-testid="transcript-live"
    >
      {turns.map((t, i) => (
        <div
          key={`${i}-${t.speaker}-${t.at}`}
          className={cn(
            "max-w-[85%] rounded-lg px-3.5 py-2.5 text-[13.5px] leading-relaxed animate-rise",
            t.speaker === "prospect"
              ? "bg-slate-800/80 text-slate-100"
              : "ml-auto border border-slate-700 text-slate-300",
          )}
          data-testid={`turn-${t.speaker}-${i}`}
        >
          <span className="mb-0.5 block text-[10.5px] font-semibold uppercase tracking-[0.14em] text-slate-500">
            {t.speaker === "prospect" ? prospectName : "You"}
          </span>
          {t.text}
        </div>
      ))}
      {pendingRep ? (
        <div className="ml-auto max-w-[85%] rounded-lg border border-slate-700 px-3.5 py-2.5 text-[13.5px] text-slate-400">
          <span className="mb-0.5 block text-[10.5px] font-semibold uppercase tracking-[0.14em] text-slate-600">
            You
          </span>
          {pendingRep}
        </div>
      ) : null}
      {interim ? (
        <div className="ml-auto max-w-[85%] px-3.5 text-[13px] italic text-slate-500">{interim}</div>
      ) : null}
    </div>
  );
}
