import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, Loader2, Mic, Play, RefreshCw, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiAudio } from "@/lib/api";
import { cn } from "@/lib/utils";
import { speechSupported } from '@/lib/voice';

const SESSION_FLAG = "repforge.audio_verified";

type MicState = "idle" | "asking" | "listening" | "heard" | "denied";
type VoiceState = "idle" | "loading" | "ready" | "failed" | 'confirm';

function markVerified() {
  try {
    sessionStorage.setItem(SESSION_FLAG, "1");
  } catch (err) {
    console.error("sessionStorage write failed", err);
  }
}

/** Pre-call audio readiness: 5-10 seconds to prove the microphone works, the
 * right buyer voice loads and the speakers play. Nothing captured here reaches
 * the transcript, the recording, the scoring or the character's memory — the
 * graded simulation only starts when "Start simulation" is pressed. */
export default function MicCheck({
  prospectName,
  simulationId,
  onStart,
  busy = false,
}: {
  prospectName: string;
  difficulty: number;
  simulationId: string;
  onStart: (typedMode?: boolean) => void;
  busy?: boolean;
}) {
  const [micState, setMicState] = useState<MicState>("idle");
  const [level, setLevel] = useState(0);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const micGeneration = useRef(0);
  const voiceGeneration = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const urlRef = useRef<string | null>(null);

  const teardown = useCallback(() => {
    micGeneration.current += 1;
    voiceGeneration.current += 1;
    abortRef.current?.abort();
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    void ctxRef.current?.close().catch(() => undefined);
    ctxRef.current = null;
    if (audioRef.current) { audioRef.current.onended = null; audioRef.current.onerror = null; audioRef.current.pause(); }
    audioRef.current = null;
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    urlRef.current = null;
  }, []);

  useEffect(() => teardown, [teardown]);

  const startMic = useCallback(async () => {
    const gen = ++micGeneration.current;
    streamRef.current?.getTracks().forEach(t => t.stop());
    setMicState("asking");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (gen !== micGeneration.current) { stream.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = stream;
      const ctx = new AudioContext();
      ctxRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      setMicState("listening");
      const tick = () => {
        if (gen !== micGeneration.current) return;
        analyser.getByteFrequencyData(data);
        const peak = data.reduce((m, v) => Math.max(m, v), 0) / 255;
        setLevel(peak);
        if (peak > 0.12) setMicState((s) => (s === "listening" ? "heard" : s));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch {
      if (gen !== micGeneration.current) return;
      setMicState("denied");
    }
  }, []);

  const testVoice = useCallback(async () => {
    const gen = ++voiceGeneration.current;
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.onended = null; audioRef.current.onerror = null; audioRef.current.pause(); }
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setVoiceState("loading");
    try {
      const blob = await apiAudio('/voice/sample', { simulation_id: simulationId }, ctrl.signal);
      if (gen !== voiceGeneration.current) return;
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { if (gen === voiceGeneration.current) setVoiceState('confirm'); };
      audio.onerror = () => { if (gen === voiceGeneration.current) setVoiceState('failed'); };
      await audio.play();
      if (gen === voiceGeneration.current) setVoiceState('confirm');
    } catch {
      if (gen !== voiceGeneration.current || ctrl.signal.aborted) return;
      setVoiceState("failed");
    }
  }, [simulationId]);

  const ready = micState === 'heard' && voiceState === 'ready' && speechSupported();

  const begin = (mode: 'verified' | 'skipped' | 'typed') => {
    if (mode === 'verified' && ready) markVerified();
    sessionStorage.setItem('repforge.audio_check', JSON.stringify({ skipped: mode === 'skipped', microphone_access: ['heard', 'listening'].includes(micState), speech_recognition_supported: speechSupported(), playback_confirmed: voiceState === 'ready', mode }));
    teardown();
    onStart(mode === 'typed');
  };

  return (
    <div className="grid flex-1 place-items-center px-5 py-10" data-testid="mic-check">
      <div className="w-full max-w-[520px] rounded-xl border border-[#1E293B] bg-[#111827] p-6">
        <h1 className="font-heading text-[22px] font-extrabold">Ready for your call?</h1>
        <p className="mt-1.5 text-[13.5px] text-slate-400">
          A ten-second check so nothing surprises you on the call. Nothing here is recorded,
          transcribed or scored.
        </p>

        <MicPanel state={micState} level={level} onTest={startMic} />
        <VoicePanel prospectName={prospectName} state={voiceState} onTest={testVoice} />
        <p className='mt-3 text-xs text-slate-400' data-testid='mic-check-limitations'>The meter detects sound, not words. {speechSupported() ? 'Speech recognition is available; verify captured words in the call transcript.' : 'This browser cannot transcribe speech. Choose typed practice.'}</p>
        {voiceState === 'confirm' ? <div className='mt-3 flex flex-wrap items-center gap-2' data-testid='audio-confirmation'><span>Did you hear the buyer?</span><Button size='sm' data-testid='audio-confirm-yes' onClick={() => setVoiceState('ready')}>Yes, I heard it</Button><Button size='sm' variant='secondary' data-testid='audio-confirm-no' onClick={() => setVoiceState('failed')}>No — try again</Button></div> : null}

        {ready ? (
          <p
            className="mt-4 flex items-center gap-2 text-[13.5px] font-semibold text-emerald-400"
            data-testid="mic-check-ready"
          >
            <CheckCircle2 className="size-4" />
            You're ready.
          </p>
        ) : null}

        <div className="mt-5 flex flex-wrap gap-3">
          <Button
            size="lg"
            className="font-semibold"
            onClick={() => begin('verified')}
            disabled={!ready || busy}
            data-testid="mic-check-start"
          >
            Start simulation
          </Button>
          <Button
            size="lg"
            variant="ghost"
            className="font-semibold text-slate-300 hover:bg-slate-800"
            onClick={() => begin('skipped')}
            disabled={busy}
            data-testid="mic-check-skip"
          >
            Skip check
          </Button>
          <Button variant='secondary' data-testid='mic-check-typed' disabled={busy} onClick={() => begin('typed')}>Use typed practice</Button>
        </div>
      </div>
    </div>
  );
}


const MIC_LABEL: Record<MicState, string> = {
  idle: "Not tested",
  asking: "Requesting permission…",
  listening: "Connected — say something",
  heard: "Input activity detected ✓",
  denied: "No microphone — you can type instead",
};

/** Microphone status + live input meter. */
function MicPanel({
  state,
  level,
  onTest,
}: {
  state: MicState;
  level: number;
  onTest: () => void;
}) {
  const bars = 14;
  return (
    <section className="mt-6 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-[13.5px] font-semibold text-slate-200">
          <Mic className="size-4 text-slate-400" />
          Microphone
        </span>
        <span
          className={cn(
            "text-[12.5px] font-semibold",
            state === "heard"
              ? "text-emerald-400"
              : state === "denied"
                ? "text-amber-400"
                : "text-slate-400",
          )}
          data-testid="mic-check-mic-status"
        >
          {MIC_LABEL[state]}
        </span>
      </div>
      <div className="mt-3 flex h-8 items-end gap-1">
        {Array.from({ length: bars }).map((_, i) => (
          <span
            key={i}
            className={cn(
              "flex-1 rounded-sm transition-[height,background-color] duration-100",
              level * bars > i ? "bg-emerald-400" : "bg-slate-800",
            )}
            style={{ height: `${20 + Math.min(1, level * 1.4) * 80 * ((i % 5) / 5 + 0.5)}%` }}
          />
        ))}
      </div>
      {state === "idle" || state === "denied" ? (
        <Button
          size="sm"
          variant="secondary"
          className="mt-3 font-semibold"
          onClick={onTest}
          data-testid="mic-check-test-mic"
        >
          {state === "denied" ? (
            <>
              <RefreshCw className="size-3.5" />
              Retry microphone access
            </>
          ) : (
            "Test my microphone"
          )}
        </Button>
      ) : null}
    </section>
  );
}

const VOICE_LABEL: Record<VoiceState, string> = {
  idle: "Not tested",
  loading: "Preparing…",
  ready: "Ready ✓",
  confirm: 'Please confirm you heard it',
  failed: "Voice connection failed",
};

/** Buyer-voice readiness: proves the speakers work AND that the character's own
 * ElevenLabs voice loaded (there is no generic-TTS fallback). */
function VoicePanel({
  prospectName,
  state,
  onTest,
}: {
  prospectName: string;
  state: VoiceState;
  onTest: () => void;
}) {
  return (
    <section className="mt-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-[13.5px] font-semibold text-slate-200">
          <Volume2 className="size-4 text-slate-400" />
          Buyer voice — {prospectName}
        </span>
        <span
          className={cn(
            "text-[12.5px] font-semibold",
            state === "ready"
              ? "text-emerald-400"
              : state === "failed"
                ? "text-red-400"
                : "text-slate-400",
          )}
          data-testid="mic-check-voice-status"
        >
          {VOICE_LABEL[state]}
        </span>
      </div>
      <Button
        size="sm"
        variant="secondary"
        className="mt-3 font-semibold"
        onClick={onTest}
        disabled={state === "loading"}
        data-testid="mic-check-test-voice"
      >
        {state === "loading" ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : (
          <Play className="size-3.5" />
        )}
        {state === "failed" ? "Retry buyer audio" : "Test buyer audio"}
      </Button>
    </section>
  );
}
