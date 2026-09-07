// Browser voice layer: Web Speech API for microphone capture (SpeechRecognition)
// and speech synthesis for the AI prospect's voice. Degrades to typed input when
// the browser has no recognition engine.
import { useCallback, useEffect, useRef, useState } from "react";
import { apiAudio, apiGet } from "@/lib/api";
import { useQuery } from '@tanstack/react-query';
import type { VoiceStatus } from '@/lib/types';

interface SpeechResultAlt {
  transcript: string;
}
interface SpeechResult {
  isFinal: boolean;
  0: SpeechResultAlt;
  length: number;
}
interface SpeechEvent {
  resultIndex: number;
  results: { length: number; [i: number]: SpeechResult };
}
interface Recognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((e: SpeechEvent) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
}
type RecognitionCtor = new () => Recognition;

function getCtor(): RecognitionCtor | null {
  const w = window as unknown as {
    SpeechRecognition?: RecognitionCtor;
    webkitSpeechRecognition?: RecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function speechSupported(): boolean {
  return getCtor() !== null;
}

export function useMic(onUtterance: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<Recognition | null>(null);
  const wantRef = useRef(false);
  const cbRef = useRef(onUtterance);
  cbRef.current = onUtterance;

  const stop = useCallback(() => {
    wantRef.current = false;
    setListening(false);
    setInterim("");
    recRef.current?.stop();
  }, []);

  /** Hard stop for ending a session: abort() discards any pending final result
   * so nothing reaches the transcript after the call is over. */
  const abort = useCallback(() => {
    wantRef.current = false;
    setListening(false);
    setInterim("");
    recRef.current?.abort();
    recRef.current = null;
  }, []);

  const start = useCallback(() => {
    const Ctor = getCtor();
    if (!Ctor) {
      setError("This browser has no speech recognition. Use the text box to reply.");
      return;
    }
    if (wantRef.current) return;
    const old = recRef.current;
    if (old) { old.onresult = null; old.onerror = null; old.onend = null; try { old.abort(); } catch { /* already stopped */ } }
    const rec = new Ctor();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    rec.onresult = (e) => {
      if (recRef.current !== rec) return;
      let live = "";
      for (let i = e.resultIndex; i < e.results.length; i += 1) {
        const r = e.results[i];
        const text = r[0].transcript.trim();
        if (r.isFinal) {
          if (text && recRef.current === rec) cbRef.current(text);
        } else {
          live += text;
        }
      }
      setInterim(live);
    };
    rec.onerror = (e) => {
      if (recRef.current !== rec) return;
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        setError("Microphone permission was denied. Use the text box to reply.");
        wantRef.current = false;
        setListening(false);
      } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
        wantRef.current = false;
        setListening(false);
        setError(e.error === 'audio-capture' ? 'No microphone was found. Connect a device or type your reply.' : 'Speech recognition lost its connection. Retry the microphone or use typed replies.');
      }
    };
    rec.onend = () => {
      if (recRef.current !== rec) return;
      if (wantRef.current) {
        try {
          rec.start();
        } catch (err) {
          // Chrome throws if start() lands while the engine is still restarting.
          console.debug("speech recognition restart ignored", err);
        }
      } else {
        setListening(false);
      }
    };
    recRef.current = rec;
    wantRef.current = true;
    setError(null);
    try {
      rec.start();
      setListening(true);
    } catch {
      // Never leave the state machine believing recognition is still wanted.
      wantRef.current = false;
      recRef.current = null;
      setListening(false);
      setError("Microphone could not be started. Use the text box to reply.");
    }
  }, []);

  useEffect(
    () => () => {
      // Explicit shutdown: recognition must not restart once this component is gone.
      wantRef.current = false;
      const rec = recRef.current;
      recRef.current = null;
      if (!rec) return;
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      try {
        rec.abort();
      } catch {
        // Already stopped by the engine — nothing to unwind.
      }
    },
    [],
  );

  return { listening, interim, error, start, stop, abort, supported: speechSupported() };
}

export type VoicePhase = "idle" | "loading" | "speaking";

function voiceErrorMessage(character: string): string {
  return `${character || "The prospect"}'s voice could not be played. No generic voice is substituted — retry to hear them.`;
}

/** Prospect voice: the approved ElevenLabs voice for this character, produced by
 * our own backend (the API key never reaches the client — we only POST text to
 * /api/voice/speak).
 *
 * There is deliberately NO browser-speech fallback: a recurring buyer must always
 * sound like the same person, so a voice failure surfaces as a visible error with
 * a retry instead of silently degrading to a robotic system voice. */
export function useProspectVoice(character = "", persona = "default", difficulty = 2, simulationId = '') {
  const [speaking, setSpeaking] = useState(false);
  const [phase, setPhase] = useState<VoicePhase>("idle");
  const [usingElevenLabs, setUsingElevenLabs] = useState(false);
  const [voiceChecked, setVoiceChecked] = useState(false);
  const [voiceReady, setVoiceReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);
  // Every speak() call takes a generation token. silence() bumps the counter, so
  // any in-flight TTS fetch or queued playback from an older generation is dropped
  // instead of starting to talk after the call has ended.
  const genRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const lastRef = useRef<{ text: string; onDone?: () => void } | null>(null);
  const characterRef = useRef(character);
  const personaRef = useRef(persona);
  const difficultyRef = useRef(difficulty);
  const simulationRef = useRef(simulationId);
  simulationRef.current = simulationId;
  characterRef.current = character;
  personaRef.current = persona;
  difficultyRef.current = difficulty;

  const voiceStatus = useQuery({ queryKey: ['voice-status'], queryFn: () => apiGet<VoiceStatus>('/voice/status'), retry: false });
  useEffect(() => { setUsingElevenLabs(Boolean(voiceStatus.data?.available)); setVoiceChecked(!voiceStatus.isPending); }, [voiceStatus.data, voiceStatus.isPending]);

  const cleanupAudio = useCallback(() => {
    if (audioRef.current) { audioRef.current.onplay = null; audioRef.current.onended = null; audioRef.current.onerror = null; }
    audioRef.current?.pause();
    audioRef.current = null;
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  }, []);

  const speak = useCallback(
    (text: string, onDone?: () => void) => {
      cleanupAudio();
      abortRef.current?.abort();
      lastRef.current = { text, onDone };
      const gen = genRef.current + 1;
      genRef.current = gen;
      setError(null);
      setPhase("loading");
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      apiAudio('/voice/speak', {
          simulation_id: simulationRef.current,
          text,
          character: characterRef.current,
          persona: personaRef.current,
          difficulty: difficultyRef.current,
        }, ctrl.signal)
        .then(async (blob) => {
          if (gen !== genRef.current) return; // session ended while audio was loading
          const url = URL.createObjectURL(blob);
          urlRef.current = url;
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onplay = () => {
            if (gen !== genRef.current) {
              audio.pause();
              return;
            }
            setSpeaking(true);
            setVoiceReady(true);
            setPhase("speaking");
          };
          audio.onended = () => {
            if (gen !== genRef.current) return;
            setSpeaking(false);
            setPhase("idle");
            cleanupAudio();
            if (gen !== genRef.current) return;
            onDone?.();
          };
          // A playback failure is NOT a finished turn: the rep never heard the
          // prospect, so surface the error and leave the mic closed until Retry.
          audio.onerror = () => {
            if (gen !== genRef.current) return;
            setSpeaking(false);
            setPhase("idle");
            cleanupAudio();
            if (gen !== genRef.current) return;
            setError(voiceErrorMessage(characterRef.current));
          };
          await audio.play();
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === "AbortError") return;
          if (gen !== genRef.current) return;
          cleanupAudio();
          setSpeaking(false);
          setPhase("idle");
          setError(voiceErrorMessage(characterRef.current));
        });
    },
    [cleanupAudio],
  );

  const retry = useCallback(() => {
    const last = lastRef.current;
    if (last) speak(last.text, last.onDone);
  }, [speak]);

  const silence = useCallback(() => {
    genRef.current += 1; // invalidate every in-flight and queued utterance
    abortRef.current?.abort();
    abortRef.current = null;
    window.speechSynthesis?.cancel();
    cleanupAudio();
    setSpeaking(false);
    setPhase("idle");
  }, [cleanupAudio]);

  useEffect(
    () => () => {
      // A request started by a destroyed component must never create audio or
      // touch React state afterwards.
      genRef.current += 1;
      abortRef.current?.abort();
      abortRef.current = null;
      window.speechSynthesis?.cancel();
      cleanupAudio();
    },
    [cleanupAudio],
  );

  return {
    speak,
    silence,
    retry,
    speaking,
    phase,
    error,
    voiceReady,
    usingElevenLabs,
    voiceChecked,
  };
}
