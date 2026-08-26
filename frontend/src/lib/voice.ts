// Browser voice layer: Web Speech API for microphone capture (SpeechRecognition)
// and speech synthesis for the AI prospect's voice. Degrades to typed input when
// the browser has no recognition engine.
import { useCallback, useEffect, useRef, useState } from "react";

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
          if (text) cbRef.current(text);
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

  return { listening, interim, error, start, stop, supported: speechSupported() };
}

export type VoicePhase = "idle" | "loading" | "speaking";

/** Prospect voice: ElevenLabs audio from our own backend when a credential is
 * configured, otherwise the browser's speech synthesis. The API key never
 * reaches the client — we only ever POST text to /api/voice/speak. */
export function useProspectVoice(persona = "default", difficulty = 2) {
  const [speaking, setSpeaking] = useState(false);
  const [phase, setPhase] = useState<VoicePhase>("idle");
  const [usingElevenLabs, setUsingElevenLabs] = useState(false);
  const [voiceChecked, setVoiceChecked] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);
  const personaRef = useRef(persona);
  const difficultyRef = useRef(difficulty);
  personaRef.current = persona;
  difficultyRef.current = difficulty;

  useEffect(() => {
    let alive = true;
    fetch("/api/voice/status")
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

  const speakBrowser = useCallback((text: string, onDone?: () => void) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      onDone?.();
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.02;
    u.pitch = 1;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find((v) => /en-US|en-GB/.test(v.lang) && !/google/i.test(v.name));
    if (preferred) u.voice = preferred;
    u.onstart = () => {
      setSpeaking(true);
      setPhase("speaking");
    };
    const done = () => {
      setSpeaking(false);
      setPhase("idle");
      onDone?.();
    };
    u.onend = done;
    u.onerror = done;
    window.speechSynthesis.speak(u);
  }, []);

  const speak = useCallback(
    (text: string, onDone?: () => void) => {
      cleanupAudio();
      if (!usingElevenLabs) {
        speakBrowser(text, onDone);
        return;
      }
      setPhase("loading");
      fetch("/api/voice/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          persona: personaRef.current,
          difficulty: difficultyRef.current,
        }),
      })
        .then(async (res) => {
          if (!res.ok) throw new Error(`tts ${res.status}`);
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          urlRef.current = url;
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onplay = () => {
            setSpeaking(true);
            setPhase("speaking");
          };
          const finish = () => {
            setSpeaking(false);
            setPhase("idle");
            cleanupAudio();
            onDone?.();
          };
          audio.onended = finish;
          audio.onerror = finish;
          await audio.play();
        })
        .catch(() => {
          // Any ElevenLabs failure degrades to the browser voice, never silence.
          speakBrowser(text, onDone);
        });
    },
    [usingElevenLabs, speakBrowser, cleanupAudio],
  );

  const silence = useCallback(() => {
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

  return { speak, silence, speaking, phase, usingElevenLabs, voiceChecked };
}
