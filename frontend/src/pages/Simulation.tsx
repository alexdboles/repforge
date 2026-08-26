import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
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
import type { Simulation, TranscriptTurn, TurnResponse } from "@/lib/types";
import { useMic, useProspectVoice } from "@/lib/voice";
import { Button } from "@/components/ui/button";
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
  const [failedLine, setFailedLine] = useState<string | null>(null);
  const openedRef = useRef(false);
  const voice = useProspectVoice(sim?.voice_persona ?? "default", sim?.difficulty ?? 2);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const turnMutation = useMutation({
    mutationFn: (text: string) =>
      apiPost<TurnResponse>(`/simulations/${id}/turns`, { text, at: seconds }),
    onSuccess: (res, text) => {
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
  const send = useCallback(
    (text: string) => {
      const clean = text.trim();
      if (!clean || turnMutation.isPending) return;
      setPendingRep(clean);
      setTurnError(null);
      turnMutation.mutate(clean);
    },
    [turnMutation],
  );

  const mic = useMic(send);

  // Speak the prospect's reply, pausing the microphone so it doesn't hear itself.
  useEffect(() => {
    if (!pendingSpeak) return;
    const line = pendingSpeak;
    setPendingSpeak(null);
    if (muted) return;
    mic.stop();
    voice.speak(line, () => {
      if (micWanted.current) mic.start();
    });
  }, [pendingSpeak, muted, mic, voice]);

  const complete = useMutation({
    mutationFn: () => apiPost<Simulation>(`/simulations/${id}/complete`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard", userId] });
      qc.invalidateQueries({ queryKey: ["history", userId] });
      qc.invalidateQueries({ queryKey: ["user", userId] });
      qc.invalidateQueries({ queryKey: ["simulation", id] });
      navigate(`/scorecard/${id}`);
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not grade the call. Please try again.";
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
    if (!sim || sim.status === "completed") return;
    const t = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [sim]);

  // speak the prospect's opening line once
  useEffect(() => {
    if (!sim || openedRef.current || muted) return;
    const opening = sim.transcript.find((t) => t.speaker === "prospect");
    if (!opening) return;
    openedRef.current = true;
    voice.speak(opening.text);
  }, [sim, muted, voice]);

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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body) {
        e.preventDefault();
        toggleMic();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

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
              {sim.mode === "business" ? "My business" : "Guided"}
            </span>
          ) : null}
          <span className="text-[11px] text-slate-500" data-testid="voice-provider">
            {!voice.voiceChecked
              ? "Checking voice…"
              : voice.usingElevenLabs
                ? "ElevenLabs voice"
                : "Browser voice"}
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
      ) : (
        <div className="mx-auto flex w-full max-w-[1100px] flex-1 flex-col px-5 py-6 sm:px-8">
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

          <section className="mt-6 flex flex-1 flex-col rounded-xl border border-[#1E293B] bg-[#0B1220]">
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
                  key={i}
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
                  onClick={() => complete.mutate()}
                  disabled={complete.isPending}
                  data-testid="end-simulation-button"
                >
                  {complete.isPending ? (
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
                  disabled={!typed.trim() || thinking}
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
                    disabled={thinking || !failedLine}
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
        </div>
      )}

      {complete.isPending ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-[#090D16]/90 backdrop-blur-sm"
          data-testid="grading-overlay"
        >
          <div className="text-center">
            <Loader2 className="mx-auto size-7 animate-spin text-sky-400" />
            <h2 className="mt-4 font-heading text-[20px] font-bold">Analysing your conversation</h2>
            <p className="mt-2 text-[13.5px] text-slate-400">
              Scoring 14 competencies against what you actually said.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
