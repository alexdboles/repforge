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
import MicCheck from "@/components/MicCheck";
import WaveBars from "@/components/WaveBars";
import TranscriptPanel from "@/components/TranscriptPanel";
import ReplyComposer from "@/components/ReplyComposer";
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
  const [callStarted, setCallStarted] = useState(false);
  const [hintsEnabled, setHintsEnabled] = useState(false);
  const callActiveRef = useRef(false);
  const busyRef = useRef(false);
  const versionRef = useRef(0);
  const requestRef = useRef<{ text: string; key: string } | null>(null);
  const {
    speak,
    silence,
    retry: retryVoice,
    speaking,
    phase: voicePhase,
    error: voiceError,
    usingElevenLabs,
    voiceChecked,
    voiceReady,
  } = useProspectVoice(
    sim?.scenario?.prospect_name ?? "",
    sim?.voice_persona ?? "default",
    sim?.difficulty ?? 2,
    id,
  );
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const turnAbortRef = useRef<AbortController | null>(null);
  useEffect(() => {
    endedRef.current = false;
    return () => { endedRef.current = true; callActiveRef.current = false; turnAbortRef.current?.abort(); };
  }, []);

  const turnMutation = useMutation({
    mutationFn: (text: string) => {
      const ctrl = new AbortController(); turnAbortRef.current = ctrl;
      return apiPost<TurnResponse>(`/simulations/${id}/turns`, { text, at: seconds, idempotency_key: requestRef.current?.key, expected_version: versionRef.current }, { signal: ctrl.signal });
    },
    onSuccess: (res) => {
      busyRef.current = false;
      if (endedRef.current) return; // late reply after End Simulation — discard entirely
      setPendingRep(null);
      setTurnError(null);
      setFailedLine(null);
      setTurns(res.transcript);
      versionRef.current = res.version;
      requestRef.current = null;
      setPendingSpeak(res.reply);
    },
    onError: (err, text) => {
      busyRef.current = false;
      void qc.invalidateQueries({ queryKey: ['simulation', id] });
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
    if (!clean || endedRef.current || !callActiveRef.current) return;
    if (busyRef.current) {
      setTyped(prev => `${prev} ${clean}`.trim());
      return;
    }
    busyRef.current = true;
    if (requestRef.current?.text !== clean) requestRef.current = { text: clean, key: crypto.randomUUID() };
    setTyped('');
    setPendingRep(clean);
    setTurnError(null);
    turnRef.current.mutate(clean);
  }, []);

  const {
    listening: micListening,
    interim: micInterim,
    error: micError,
    start: startMic,
    stop: stopMic,
    abort: abortMic,
    supported: micSupported,
  } = useMic(send);

  const activate = useMutation({
    mutationFn: () => apiPost<Simulation>(`/simulations/${id}/activate`),
    onSuccess: data => { qc.setQueryData(['simulation', id], data); setCallStarted(true); callActiveRef.current = true; },
    onError: () => toast.error('Could not start this call. Retry or return to History.'),
  });
  const abandon = useMutation({ mutationFn: () => apiPost<Simulation>(`/simulations/${id}/abandon`), onSuccess: () => navigate('/history') });

  // Speak the prospect's reply, pausing the microphone so it doesn't hear itself.
  useEffect(() => {
    if (!pendingSpeak) return;
    const line = pendingSpeak;
    setPendingSpeak(null);
    if (muted || endedRef.current) return;
    stopMic();
    speak(line, () => {
      if (micWanted.current && !endedRef.current) startMic();
    });
  }, [pendingSpeak, muted, speak, startMic, stopMic]);

  const coachingOn = Boolean(sim && sim.difficulty <= 2 && hintsEnabled);
  const { data: hint, isFetching: hintLoading } = useQuery({
    queryKey: ["hint", id, turns.length],
    queryFn: () => apiGet<Hint>(`/simulations/${id}/hint`),
    enabled: coachingOn && callStarted && turns.length > 0 && !turnMutation.isPending && !ended,
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
      if (err instanceof ApiError && err.status === 422) {
        endedRef.current = false; callActiveRef.current = true; setEnded(false);
        toast.error('No speech had been accepted yet. Wait for your reply to save, then end the call.');
        return;
      }
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
      versionRef.current = sim.version ?? 0;
      if (sim.status === 'active') { setCallStarted(true); callActiveRef.current = true; }
      if (['grading', 'grading_failed', 'ending', 'analyzing'].includes(sim.status)) {
        endedRef.current = true; setEnded(true); setCallStarted(true);
        setGradeError(sim.grading_error || 'The call is frozen. Retry grading to recover your report.');
      }
      if (sim.status === 'abandoned') navigate('/history', { replace: true });
      if (sim.status === "completed") navigate(`/scorecard/${sim.id}`, { replace: true });
    }
  }, [sim, hydrated, navigate]);

  useEffect(() => {
    if (sim && turnError) { setTurns(sim.transcript); versionRef.current = sim.version ?? 0; }
  }, [sim, turnError]);

  // call timer
  useEffect(() => {
    if (!sim || !callStarted) return;
    if (ended || sim.ended_at) { if (sim.ended_at) setSeconds(sim.duration_seconds); return; }
    const started = Date.parse(sim.call_started_at ?? sim.started_at);
    const tick = () => setSeconds(Math.max(0, Math.floor((Date.now() - started) / 1000)));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [sim, callStarted, ended]);

  // speak the prospect's opening line once
  useEffect(() => {
    if (!sim || !callStarted || openedRef.current || muted || endedRef.current) return;
    const opening = sim.transcript.find((t) => t.speaker === "prospect");
    if (!opening) return;
    openedRef.current = true;
    speak(opening.text);
  }, [sim, muted, speak, callStarted]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, pendingRep]);

  const toggleMic = () => {
    if (!callStarted || sim?.status !== 'active' || endedRef.current || complete.isPending || busyRef.current) return;
    if (micListening) {
      micWanted.current = false;
      stopMic();
    } else {
      micWanted.current = true;
      silence();
      startMic();
    }
  };

  const toggleMicRef = useRef(toggleMic);
  toggleMicRef.current = toggleMic;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat && e.target === document.body) {
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
    const thinking = turnMutation.isPending || voicePhase === "loading";
  // Only an in-flight turn blocks sending. Voice loading must never disable the
  // reply controls — the rep would silently lose the line they just typed.
  const sending = turnMutation.isPending || ended || !callStarted;

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
      : micListening
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
          {sim?.is_demo ? <span className='text-xs text-sky-300' data-testid='simulation-demo-label'>Demo scenario · fictional buyer</span> : null}
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
            {!voiceChecked
              ? "Preparing voice…"
              : voiceError
                ? "Voice failed"
                : usingElevenLabs
                  ? `ElevenLabs · ${voiceReady ? 'audio played successfully' : 'voice configured, playback not confirmed'}`
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
      ) : !callStarted ? (<>
        <section className='mx-auto mt-6 w-full max-w-[620px] px-5' data-testid='pre-call-brief'>
          <h2 className='font-heading text-lg font-bold' data-testid='brief-heading'>{sim.is_demo ? 'Your 2-minute demo brief' : 'Your call brief'}</h2>
          <p className='mt-2 text-sm text-slate-300' data-testid='brief-product'><strong>You sell:</strong> {scenario.product_sheet?.one_liner || scenario.product}</p>
          <p className='mt-2 text-sm text-slate-300' data-testid='brief-buyer'><strong>Buyer:</strong> {scenario.prospect_name}, {scenario.prospect_role} · {scenario.company}</p>
          <p className='mt-2 text-sm text-slate-300' data-testid='brief-objective'><strong>Objective:</strong> {scenario.objective}</p>
          {sim.is_demo ? <p className='mt-2 text-xs text-slate-400' data-testid='demo-timing-note'>Aim for two minutes, then end the call for coaching. This is a target, not a time limit.</p> : null}
          <Button variant='ghost' className='mt-3 text-slate-300' data-testid='setup-abandon' onClick={() => abandon.mutate()} disabled={abandon.isPending}>Leave this preparation</Button>
        </section>
        <MicCheck
          simulationId={id}
          prospectName={scenario.prospect_name}
          difficulty={sim.difficulty}
          busy={activate.isPending}
          onStart={(typedMode) => { if (typedMode) setMuted(true); activate.mutate(); }}
        />
        </>
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

          <details className='mt-4 rounded-lg border border-slate-800 p-3 text-sm' data-testid='call-tip-sheet'><summary className='cursor-pointer text-slate-300' data-testid='call-tip-sheet-toggle'>Product facts & call brief</summary><p className='mt-3' data-testid='call-tip-product'>{scenario.product_sheet?.one_liner || scenario.product}</p><p className='mt-2' data-testid='call-tip-pricing'>{scenario.product_sheet?.pricing}</p><p className='mt-2' data-testid='call-tip-known'>{scenario.known}</p><ul className='mt-2 list-disc pl-5'>{scenario.product_sheet?.limitations.map((l, i) => <li data-testid={`call-tip-limit-${i}`} key={l}>{l}</li>)}</ul></details>
          {sim.difficulty <= 2 ? <Button variant='ghost' className='mt-2 self-start text-sky-300' data-testid='enable-live-hints' onClick={() => setHintsEnabled(v => !v)} disabled={ended}>{hintsEnabled ? 'Hide live coaching' : 'Use optional live coaching (assisted practice)'}</Button> : null}

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

            <TranscriptPanel
              turns={turns}
              prospectName={scenario.prospect_name}
              pendingRep={pendingRep}
              interim={micInterim}
              scrollRef={scrollRef}
            />

            <WaveBars
              active={speaking || micListening}
              tone={speaking ? "prospect" : micListening ? "rep" : "idle"}
            />

            <div className="border-t border-[#1E293B] px-5 py-4">
              {voiceError ? (
                <div
                  className="mb-3 flex flex-wrap items-center gap-3 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-[12.5px] text-red-200"
                  data-testid="voice-error"
                >
                  <span className="min-w-0 flex-1">{voiceError}</span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => retryVoice()}
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
                  disabled={!callStarted || ended || sim.status !== 'active' || complete.isPending || sending || !micSupported}
                  data-testid="mic-toggle-button"
                  className={cn(
                    "font-semibold",
                    micListening
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-slate-100 text-slate-900 hover:bg-white",
                  )}
                >
                  {micListening ? <Mic className="size-4" /> : <MicOff className="size-4" />}
                  {micListening ? "Microphone live" : "Talk to prospect"}
                </Button>

                <Button
                  variant="ghost"
                  size="icon-lg"
                  onClick={() => {
                    setMuted((m) => !m);
                    silence();
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
                    callActiveRef.current = false;
                    setEnded(true);
                    micWanted.current = false;
                    abortMic();
                    silence();
                    turnMutation.reset();
                    setPendingRep(null);
                    setPendingSpeak(null);
                    setTurnError(null);
                    complete.mutate();
                  }}
                  disabled={complete.isPending || ended || !turns.some(t => t.speaker === 'rep') && !pendingRep}
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

              <ReplyComposer
                typed={typed}
                onTyped={setTyped}
                onSend={(text) => { silence(); stopMic(); send(text); }}
                sending={sending}
                micSupported={micSupported}
                turnError={turnError}
                failedLine={failedLine}
              />
              {micError ? (
                <p className="mt-2 text-[12.5px] text-amber-400" data-testid="mic-error">
                  {micError}
                </p>
              ) : (
                <p className="mt-2 text-[12px] text-slate-500">
                  Press Space outside controls to toggle the microphone. Final speech received while a reply is pending is preserved in your draft.
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
