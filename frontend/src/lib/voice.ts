// Browser voice layer: Web Speech API for microphone capture (SpeechRecognition)
// and speech synthesis for the AI prospect's voice. Degrades to typed input when
// the browser has no recognition engine.
import { useCallback, useEffect, useRef, useState } from "react";
import { authHeaders } from "@/lib/api";

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
    const rec = new Ctor();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    rec.onresult = (e) => {
      let live = "";
      for (let i = e.resultIndex; i < e.results.length; i += 1) {
        const r = e.results[i];
        const text = r[0].transcript.trim();
        if (r.isFinal) {
          if (text && wantRef.current) cbRef.current(text);
        } else {
          live += text;
        }
      }
      setInterim(live);
    };
    rec.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        setError("Microphone permission was denied. Use the text box to reply.");
        wantRef.current = false;
        setListening(false);
      }
    };
    rec.onend = () => {
      if (wantRef.current) {
        try {
          rec.start();
        } catch {
          /* already restarting */
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
      setError("Microphone could not be started. Use the text box to reply.");
    }
  }, []);

  useEffect(() => () => recRef.current?.abort(), []);

  return { listening, interim, error, start, stop, abort, supported: speechSupported() };
}

export type VoicePhase = "idle" | "loading" | "speaking";

/** Prospect voice: the approved ElevenLabs voice for this character, produced by
 * our own backend (the API key never reaches the client — we only POST text to
 * /api/voice/speak).
 *
 * There is deliberately NO browser-speech fallback: a recurring buyer must always
 * sound like the same person, so a voice failure surfaces as a visible error with
 * a retry instead of silently degrading to a robotic system voice. */
export function useProspectVoice(character = "", persona = "default", difficulty = 2) {
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
  characterRef.current = character;
  personaRef.current = persona;
  difficultyRef.current = difficulty;

  useEffect(() => {
    let alive = true;
    fetch("/api/voice/status", { credentials: "include", headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { available?: boolean } | null) => {
        if (!alive) return;
        if (d) setUsingElevenLabs(Boolean(d.available));
        setVoiceChecked(true);
      })
      .catch(() => {
        if (alive) setVoiceChecked(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  const cleanupAudio = useCallback(() => {
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
      fetch("/api/voice/speak", {
        method: "POST",
        credentials: "include",
        signal: ctrl.signal,
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          text,
          character: characterRef.current,
          persona: personaRef.current,
          difficulty: difficultyRef.current,
        }),
      })
        .then(async (res) => {
          if (!res.ok) throw new Error(`tts ${res.status}`);
          const blob = await res.blob();
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
          const finish = () => {
            setSpeaking(false);
            setPhase("idle");
            cleanupAudio();
            if (gen !== genRef.current) return;
            onDone?.();
          };
          audio.onended = finish;
          audio.onerror = finish;
          await audio.play();
        })
        .catch((err: unknown) => {
          if (gen !== genRef.current) return;
          if (err instanceof DOMException && err.name === "AbortError") return;
          setSpeaking(false);
          setPhase("idle");
          setError(
            `${characterRef.current || "The prospect"}'s voice could not be loaded. No generic voice is substituted — retry to hear them.`,
          );
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
