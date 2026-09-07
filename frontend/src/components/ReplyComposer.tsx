import { RotateCcw, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Typed-reply lane for the live call: always available (headsets fail, rooms are
 * noisy, some browsers have no speech recognition) plus the retry affordance for a
 * turn whose AI reply failed — the rep's words are never lost. */
export default function ReplyComposer({
  typed,
  onTyped,
  onSend,
  sending,
  micSupported,
  turnError,
  failedLine,
}: {
  typed: string;
  onTyped: (value: string) => void;
  onSend: (text: string) => void;
  sending: boolean;
  micSupported: boolean;
  turnError: string | null;
  failedLine: string | null;
}) {
  return (
    <>
      <label htmlFor='reply-draft' className='mt-3 block text-xs text-slate-400' data-testid='typed-reply-label'>Your reply draft{sending ? ' — saved here while the buyer responds' : ''}</label>
      <form
        className="mt-3 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          onSend(typed);
        }}
      >
        <Input
          id='reply-draft'
          maxLength={2000}
          value={typed}
          onChange={(e) => onTyped(e.target.value)}
          placeholder={
            micSupported
              ? "Or type what you'd say (useful without a microphone)"
              : "This browser has no speech recognition — type what you'd say"
          }
          className="border-slate-700 bg-slate-900 text-slate-100 placeholder:text-slate-500"
          data-testid="typed-reply-input"
        />
        <Button
          type="submit"
          variant="secondary"
          disabled={!typed.trim() || sending}
          data-testid="send-typed-reply-button"
        >
          <Send className="size-4" />
          Say it
        </Button>
      </form>
      {turnError ? (
        <div
          className="mt-3 flex flex-wrap items-center gap-3 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-[12.5px] text-amber-200"
          data-testid="turn-error"
        >
          <span className="min-w-0 flex-1">
            {turnError} Review the saved transcript before continuing.
          </span>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => failedLine && onSend(failedLine)}
            disabled={sending || !failedLine}
            data-testid="retry-turn-button"
          >
            <RotateCcw className="size-3.5" />
            Retry
          </Button>
        </div>
      ) : null}
    </>
  );
}
