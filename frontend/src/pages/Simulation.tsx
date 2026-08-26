import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Compass,
  Loader2,
  Mic,
  MicOff,
  PhoneOff,
  RotateCcw,
  Send,
  Target,
  Volume2,
  VolumeX,
} from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { formatDuration, getUserId } from "@/lib/profile";
import type { Hint } from "@/lib/types";
import type { Simulation, TranscriptTurn, TurnResponse } from "@/lib/types";
import { useMic, useProspectVoice } from "@/lib/voice";
import { Button } from "@/components/ui/button";
import MicCheck, { audioAlreadyVerified } from "@/components/MicCheck";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

function initials(name: string) {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function SimulationPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const userId = getUserId();
  const qc = useQueryClient();

  const { data: sim, isLoading, isError } = useQuery({
    queryKey: ["simulation", id],
    queryFn: () => apiGet<Simulation>(`/simulations/${id}`),
    retry: false,
  });

  const [turns, setTurns] = useState<TranscriptTurn[]>([]);
  const [seconds, setSeconds] = useState(0);
  const [typed, setTyped] = useState("");
  const [muted, setMuted] = useState(false);
  const [pendingRep, setPendingRep] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [pendingSpeak, setPendingSpeak] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
  const [showExample, setShowExample] = useState(false);
  // Hard session boundary: once true, nothing may reach the transcript or the voice layer.
  const [ended, setEnded] = useState(false);
  // Ref mirror of `ended` — callbacks captured before the click (mutation
  // handlers, mic results, TTS completion) read the ref, never a stale closure.
  const endedRef = useRef(false);
  const [failedLine, setFailedLine] = useState<string | null>(null);
  const [gradeError, setGradeError] = useState<string | null>(null);
  const openedRef = useRef(false);
  // Audio readiness gate: the graded call (and the prospect's opening line) only
  // begins once the rep has passed — or skipped — the check.
  const [callStarted, setCallStarted] = useState(audioAlreadyVerified());
  const voice = useProspectVoice(
    sim?.scenario?.prospect_name ?? "",
    sim?.voice_persona ?? "default",
    sim?.difficulty ?? 2,
  );
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const turnMutation = useMutation({
    mutationFn: (text: string) =>
      apiPost<TurnResponse>(`/simulations/${id}/turns`, { text, at: seconds }),
    onSuccess: (res, text) => {
      if (endedRef.current) return; // late reply after End Simulation — discard entirely
      setPendingRep(null);
      setTurnError(null);
      setFailedLine(null);
      setTyped("");
      setTurns((prev) => [
        ...prev,
        { speaker: "rep", text, at: seconds },
        { speaker: "prospect", text: res.reply, at: seconds },
      ]);
      setPendingSpeak(res.reply);
    },
    onError: (err, text) => {
      setPendingRep(null);
      if (endedRef.current) return;
      setFailedLine(text);
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "The prospect could not be reached.";
      setTurnError(detail);
      toast.error(detail);
    },
  });

  const micWanted = useRef(false);
  // The mutation object is a new value on every render; keeping it in a ref lets
  // send() stay referentially stable for useMic without ever going stale.
  const turnRef = useRef(turnMutation);
  turnRef.current = turnMutation;
  const send = useCallback((text: string) => {
    const clean = text.trim();
    if (!clean || turnRef.current.isPending || endedRef.current) return;
    setPendingRep(clean);
    setTurnError(null);
    turnRef.current.mutate(clean);
  }, []);

  const mic = useMic(send);

  // Speak the prospect's reply, pausing the microphone so it doesn't hear itself.
  useEffect(() => {
    if (!pendingSpeak) return;
    const line = pendingSpeak;
    setPendingSpeak(null);
    if (muted || endedRef.current) return;
    mic.stop();
    voice.speak(line, () => {
      if (micWanted.current && !endedRef.current) mic.start();
    });
  }, [pendingSpeak, muted, mic, voice]); // mic/voice are stable hook APIs

  const coachingOn = Boolean(sim && sim.difficulty <= 2);
  const { data: hint, isFetching: hintLoading } = useQuery({
    queryKey: ["hint", id, turns.length],
    queryFn: () => apiGet<Hint>(`/simulations/${id}/hint`),
    enabled: coachingOn && turns.length > 0 && !turnMutation.isPending && !ended,
    retry: false,
    staleTime: Infinity,
  });

  useEffect(() => {
    setShowExample(false);
  }, [turns.length]);

  const complete = useMutation({
    mutationFn: () => apiPost<Simulation>(`/simulations/${id}/complete`),
    onSuccess: () => {
      setGradeError(null);
      qc.invalidateQueries({ queryKey: ["dashboard", userId] });
      qc.invalidateQueries({ queryKey: ["history", userId] });
      qc.invalidateQueries({ queryKey: ["user", userId] });
      qc.invalidateQueries({ queryKey: ["simulation", id] });
      navigate(`/scorecard/${id}`);
    },
    onError: (err) => {
      // Grading failed — keep the call frozen but show a retry instead of a
      // spinner that never resolves.
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not grade the call. Please try again.";
      setGradeError(detail);
      toast.error(detail);
    },
  });

  // hydrate transcript once
  useEffect(() => {
    if (sim && !hydrated) {
      setTurns(sim.transcript);
      setHydrated(true);
      if (sim.status === "completed") navigate(`/scorecard/${sim.id}`, { replace: true });
    }
  }, [sim, hydrated, navigate]);

  // call timer
  useEffect(() => {
    if (!sim || sim.status === "completed" || !callStarted) return;
    const t = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [sim, callStarted]);

  // speak the prospect's opening line once
  useEffect(() => {
    if (!sim || !callStarted || openedRef.current || muted || endedRef.current) return;
    const opening = sim.transcript.find((t) => t.speaker === "prospect");
    if (!opening) return;
    openedRef.current = true;
    voice.speak(opening.text);
  }, [sim, muted, voice, callStarted]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, pendingRep]);

  const toggleMic = () => {
    if (mic.listening) {
      micWanted.current = false;
      mic.stop();
    } else {
      micWanted.current = true;
      voice.silence();
      mic.start();
    }
  };

  const toggleMicRef = useRef(toggleMic);
  toggleMicRef.current = toggleMic;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body) {
        e.preventDefault();
        toggleMicRef.current();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!userId) return <Navigate to="/" replace />;

  if (isError) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#090D16] p-6 text-slate-200">
        <div className="max-w-md text-center" data-testid="simulation-error">
          <h1 className="font-heading text-[22px] font-bold">This simulation is unavailable</h1>
          <p className="mt-2 text-[13.5px] text-slate-400">
            The session could not be loaded. Start a new one from the training library.
          </p>
          <Button className="mt-5" onClick={() => navigate("/training")} data-testid="simulation-error-back">
            Back to training
          </Button>
        </div>
      </div>
    );
  }

  const scenario = sim?.scenario;
  const speaking = voice.speaking;
  const thinking = turnMutation.isPending || voice.phase === "loading";
  // Only an in-flight turn blocks sending. Voice loading must never disable the
  // reply controls — the rep would silently lose the line they just typed.
  const sending = turnMutation.isPending;

  const phase = thinking
    ? {
        label: `${scenario?.prospect_name?.split(" ")[0] ?? "Prospect"} is thinking`,
        className: "bg-amber-500/15 text-amber-300",
        dot: "bg-amber-400 animate-pulse",
      }
    : speaking
      ? {
          label: `${scenario?.prospect_name?.split(" ")[0] ?? "Prospect"} is speaking`,
          className: "bg-sky-500/15 text-sky-300",
          dot: "bg-sky-400 animate-pulse",
        }
      : mic.listening
        ? {
            label: "Listening — speak now",
            className: "bg-emerald-500/15 text-emerald-300",
            dot: "bg-emerald-400 animate-pulse",
          }
        : {
            label: "Your turn — microphone off",
            className: "bg-slate-700/40 text-slate-300",
            dot: "bg-slate-500",
          };

  return (
    <div className="flex min-h-screen flex-col bg-[#090D16] text-slate-100" data-testid="simulation-page">
      <header className="border-b border-[#1E293B]">
        <div className="mx-auto flex max-w-[1100px] flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4 sm:px-8">
          <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            <span
              className={cn(
                "size-2 rounded-full",
                sim ? "animate-pulse bg-red-500" : "bg-slate-600",
              )}
            />
            {sim ? "Live simulation" : "Connecting"}
          </span>
          <span className="text-[13px] text-slate-400" data-testid="simulation-exercise">
            {sim?.exercise_name} · Level {sim?.difficulty} {sim?.difficulty_name}
          </span>
          {sim ? (
            <span
              className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] font-semibold text-slate-300"
              data-testid="simulation-mode"
            >
              {sim.mode === "business"
                ? "My business"
                : sim.mode === "journey"
                  ? "Journey"
                  : "Guided"}
            </span>
          ) : null}
          {sim?.prior_context ? (
            <span
              className="rounded-full bg-violet-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-violet-300"
              data-testid="memory-badge"
            >
              Remembers your earlier calls
            </span>
          ) : null}
          <span className="text-[11px] text-slate-500" data-testid="voice-provider">
            {!voice.voiceChecked
              ? "Preparing voice…"
              : voice.error
                ? "Voice failed"
                : voice.usingElevenLabs
                  ? `ElevenLabs voice · ${sim?.scenario?.prospect_name?.split(" ")[0] ?? "prospect"}`
                  : "Voice unavailable"}
          </span>
          <span
            className="ml-auto font-mono text-[16px] tabular-nums text-slate-200"
            data-testid="call-timer"
          >
            {formatDuration(seconds)}
          </span>
        </div>
      </header>

      {isLoading || !sim || !scenario ? (
        <div className="grid flex-1 place-items-center" data-testid="simulation-loading">
          <div className="flex items-center gap-3 text-slate-400">
            <Loader2 className="size-5 animate-spin" />
            Preparing your prospect…
          </div>
        </div>
      ) : !callStarted ? (
        <MicCheck
          prospectName={scenario.prospect_name}
          difficulty={sim.difficulty}
          onStart={() => setCallStarted(true)}
        />
      ) : (
        <div className="mx-auto flex w-full max-w-[1100px] flex-1 flex-col px-5 py-6 sm:px-8">
          {sim.mode === "moment" ? (
            <section
              className="mb-4 rounded-xl border border-sky-500/30 bg-sky-500/[0.08] p-5"
              data-testid="moment-retry-banner"
            >
              <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-300">
                Retrying coaching moment · {sim.moment_label}
              </span>
              <p className="mt-2 text-[13.5px] leading-relaxed text-slate-200">
                <span className="font-semibold">Situation: </span>
                {sim.moment_situation}
              </p>
              <p className="mt-1.5 text-[13.5px] leading-relaxed text-sky-200">
                <span className="font-semibold">Your objective: </span>
                {sim.moment_objective}
              </p>
              <p className="mt-2 text-[12px] text-slate-400">
                Your original score of {sim.origin_score} stays exactly as it was — this is practice
                after the assessment.
              </p>
            </section>
          ) : null}
          <section className="flex flex-wrap items-center gap-5 rounded-xl border border-[#1E293B] bg-[#111827] p-5">
            <div
              className={cn(
                "grid size-14 shrink-0 place-items-center rounded-full bg-slate-800 font-heading text-[17px] font-bold",
                speaking && "animate-pulse-ring",
              )}
            >
              {initials(scenario.prospect_name)}
            </div>
            <div className="min-w-0">
              <div className="font-heading text-[18px] font-bold" data-testid="prospect-name">
                {scenario.prospect_name}
              </div>
              <div className="text-[13px] text-slate-400">
                {scenario.prospect_role} · {scenario.company} · {scenario.company_size}
              </div>
            </div>
            <div className="ml-auto flex items-center gap-2 rounded-md bg-slate-800/70 px-3 py-2 text-[12.5px] text-slate-300">
              <Target className="size-3.5 text-sky-400" />
              <span className="max-w-[340px]" data-testid="simulation-objective">
                {scenario.objective}
              </span>
            </div>
          </section>

          <div className={cn("mt-6 grid flex-1 gap-4", coachingOn && "lg:grid-cols-[1fr_320px]")}>
          <section className="flex flex-1 flex-col rounded-xl border border-[#1E293B] bg-[#0B1220]">
            <div className="flex items-center justify-between border-b border-[#1E293B] px-5 py-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                Conversation
              </span>
              <span
                className={cn(
                  "flex items-center gap-2 rounded-full px-2.5 py-1 text-[12px] font-semibold",
                  phase.className,
                )}
                aria-live="polite"
                data-testid="voice-status"
              >
                <span className={cn("size-2 rounded-full", phase.dot)} />
                {phase.label}
              </span>
            </div>

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
                    {t.speaker === "prospect" ? scenario.prospect_name : "You"}
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
              {mic.interim ? (
                <div className="ml-auto max-w-[85%] px-3.5 text-[13px] italic text-slate-500">
                  {mic.interim}
                </div>
              ) : null}
            </div>

            <div className="flex h-14 items-end justify-center gap-1 px-6 pb-2">
              {Array.from({ length: 28 }).map((_, i) => (
                <span
                  key={i}
                  className={cn(
                    "flex-1 origin-bottom rounded-sm transition-colors",
                    speaking ? "bg-sky-400/80" : mic.listening ? "bg-emerald-400/70" : "bg-slate-800",
                  )}
                  style={{
                    height: `${20 + ((i * 37) % 70)}%`,
                    animation:
                      speaking || mic.listening
                        ? `wave ${0.8 + (i % 5) * 0.12}s ease-in-out ${i * 40}ms infinite`
                        : undefined,
                    transform: speaking || mic.listening ? undefined : "scaleY(0.2)",
                  }}
                />
              ))}
            </div>

            <div className="border-t border-[#1E293B] px-5 py-4">
              {voice.error ? (
                <div
                  className="mb-3 flex flex-wrap items-center gap-3 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-[12.5px] text-red-200"
                  data-testid="voice-error"
                >
                  <span className="min-w-0 flex-1">{voice.error}</span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => voice.retry()}
                    data-testid="voice-retry-button"
                  >
                    <RotateCcw className="size-3.5" />
                    Retry voice
                  </Button>
                </div>
              ) : null}
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  size="lg"
                  onClick={toggleMic}
                  data-testid="mic-toggle-button"
                  className={cn(
                    "font-semibold",
                    mic.listening
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-slate-100 text-slate-900 hover:bg-white",
                  )}
                >
                  {mic.listening ? <Mic className="size-4" /> : <MicOff className="size-4" />}
                  {mic.listening ? "Microphone live" : "Talk to prospect"}
                </Button>

                <Button
                  variant="ghost"
                  size="icon-lg"
                  onClick={() => {
                    setMuted((m) => !m);
                    voice.silence();
                  }}
                  data-testid="speaker-toggle-button"
                  className="text-slate-300 hover:bg-slate-800"
                  aria-label={muted ? "Unmute prospect voice" : "Mute prospect voice"}
                >
                  {muted ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}
                </Button>

                <Button
                  variant="destructive"
                  size="lg"
                  className="ml-auto font-semibold"
                  onClick={() => {
                    // Terminate the live session first, then analyse the frozen transcript.
                    endedRef.current = true;
                    setEnded(true);
                    micWanted.current = false;
                    mic.abort();
                    voice.silence();
                    turnMutation.reset();
                    setPendingRep(null);
                    setPendingSpeak(null);
                    setTurnError(null);
                    complete.mutate();
                  }}
                  disabled={complete.isPending || ended}
                  data-testid="end-simulation-button"
                >
                  {ended || complete.isPending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Grading your call…
                    </>
                  ) : (
                    <>
                      <PhoneOff className="size-4" />
                      End simulation
                    </>
                  )}
                </Button>
              </div>

              <form
                className="mt-3 flex gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  send(typed);
                }}
              >
                <Input
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={
                    mic.supported
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
                    {turnError} Your words were kept — retry when ready.
                  </span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => failedLine && send(failedLine)}
                    disabled={sending || !failedLine}
                    data-testid="retry-turn-button"
                  >
                    <RotateCcw className="size-3.5" />
                    Retry
                  </Button>
                </div>
              ) : null}
              {mic.error ? (
                <p className="mt-2 text-[12.5px] text-amber-400" data-testid="mic-error">
                  {mic.error}
                </p>
              ) : (
                <p className="mt-2 text-[12px] text-slate-500">
                  Press the space bar to toggle your microphone. No coaching appears until the call
                  ends.
                </p>
              )}
            </div>
          </section>

          {coachingOn ? (
            <aside
              className="rounded-xl border border-sky-500/25 bg-sky-500/[0.06] p-5"
              data-testid="coaching-rail"
            >
              <div className="flex items-center gap-2">
                <Compass className="size-4 text-sky-400" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-300">
                  Live coaching · Level {sim.difficulty}
                </span>
              </div>
              {hintLoading && !hint ? (
                <div className="mt-4 space-y-2" data-testid="coaching-loading">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-3 animate-pulse rounded bg-slate-700/60" />
                  ))}
                </div>
              ) : hint ? (
                <div className="mt-4">
                  <div className="text-[12px] font-semibold text-slate-400" data-testid="hint-stage">
                    {hint.stage}
                  </div>
                  <p className="mt-1.5 text-[14px] font-medium leading-relaxed" data-testid="hint-goal">
                    {hint.goal}
                  </p>
                  {hint.reveal_example || showExample ? (
                    <p
                      className="mt-3 rounded-md bg-slate-900/70 p-3 text-[13px] italic leading-relaxed text-sky-200"
                      data-testid="hint-example"
                    >
                      “{hint.example}”
                    </p>
                  ) : (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="mt-3"
                      onClick={() => setShowExample(true)}
                      data-testid="hint-reveal-example"
                    >
                      Show example wording
                    </Button>
                  )}
                  {hint.avoid ? (
                    <p className="mt-3 border-t border-slate-700/70 pt-3 text-[12.5px] text-amber-300" data-testid="hint-avoid">
                      Watch out: {hint.avoid}
                    </p>
                  ) : null}
                </div>
              ) : (
                <p className="mt-4 text-[13px] text-slate-400" data-testid="coaching-idle">
                  Say something to {scenario.prospect_name.split(" ")[0]} and your next coaching step
                  appears here.
                </p>
              )}
              <p className="mt-5 border-t border-slate-700/70 pt-3 text-[11.5px] leading-relaxed text-slate-500">
                Coaching is only available on Levels 1 and 2. From Level 3 the wheels come off — you
                run the conversation yourself.
              </p>
            </aside>
          ) : null}
          </div>
        </div>
      )}

      {ended || complete.isPending ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-[#090D16]/90 backdrop-blur-sm"
          data-testid="grading-overlay"
        >
          {gradeError ? (
            <div className="max-w-md text-center" data-testid="grading-error">
              <h2 className="font-heading text-[20px] font-bold">Call ended — grading failed</h2>
              <p className="mt-2 text-[13.5px] text-slate-300">
                {gradeError} Your conversation is saved, so nothing is lost.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-3">
                <Button
                  onClick={() => {
                    setGradeError(null);
                    complete.mutate();
                  }}
                  disabled={complete.isPending}
                  data-testid="grading-retry-button"
                  className="font-semibold"
                >
                  <RotateCcw className="size-4" />
                  Try grading again
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate("/training")}
                  data-testid="grading-exit-button"
                  className="border-slate-700 bg-transparent font-semibold text-slate-200 hover:bg-slate-800"
                >
                  Back to training
                </Button>
              </div>
            </div>
          ) : (
          <div className="text-center">
            <Loader2 className="mx-auto size-7 animate-spin text-sky-400" />
            <h2 className="mt-4 font-heading text-[20px] font-bold">Simulation complete</h2>
            <p className="mt-1.5 text-[14px] text-slate-300">Analysing your performance…</p>
            <ul className="mx-auto mt-5 space-y-1.5 text-left text-[13px] text-slate-400">
              <li>· Conversation locked — microphone and prospect disconnected</li>
              <li>· Processing transcript</li>
              <li>· Evaluating discovery, listening and objection handling</li>
              <li>· Identifying coaching opportunities</li>
              <li>· Building your scorecard</li>
            </ul>
          </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
