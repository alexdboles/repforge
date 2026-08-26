import { Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { CheckCircle2, Loader2, Play, XCircle } from "lucide-react";
import { toast } from "sonner";
import { apiGet, authHeaders } from "@/lib/api";
import { getUserId } from "@/lib/profile";
import type { CastVoice } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { Button } from "@/components/ui/button";

const TEST_LINES = [
  "Okay, I understand what you're saying, but honestly we're pretty happy with what we use today. So what would actually make this worth changing?",
  "Hmm… maybe. I'm just not convinced that's really the problem we're trying to solve.",
  "I've got two minutes. Give me the short version.",
];

/** Internal QA screen: every recurring buyer has one permanent voice, and this is
 * where a human listens to each one before it ships. A 200 from ElevenLabs is not
 * approval — the ear is. */
export default function VoiceCast() {
  const userId = getUserId();
  const [playing, setPlaying] = useState<string | null>(null);
  const [line, setLine] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["voice-cast"],
    queryFn: () => apiGet<CastVoice[]>("/voice/cast"),
    retry: false,
  });

  const preview = async (character: string) => {
    audioRef.current?.pause();
    setPlaying(character);
    try {
      const res = await fetch("/api/voice/speak", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ text: TEST_LINES[line], character, difficulty: 3 }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const audio = new Audio(URL.createObjectURL(await res.blob()));
      audioRef.current = audio;
      audio.onended = () => setPlaying(null);
      await audio.play();
    } catch {
      setPlaying(null);
      toast.error(`${character}'s voice could not be produced.`);
    }
  };

  if (!userId) return <Navigate to="/" replace />;

  return (
    <AppShell>
      <div data-testid="voice-cast-page">
        <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">Voice cast QA</h1>
        <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
          Every recurring buyer keeps one permanent ElevenLabs voice — no random assignment and no
          browser-speech fallback. Listen to each one on the same test line before shipping.
        </p>

        <div className="mt-6 flex flex-wrap gap-2" data-testid="voice-test-lines">
          {TEST_LINES.map((l, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setLine(i)}
              data-testid={`voice-test-line-${i}`}
              className={`rounded-full border px-3 py-1.5 text-[12.5px] font-semibold transition-colors ${
                line === i
                  ? "border-primary bg-accent text-foreground"
                  : "border-border bg-card text-muted-foreground hover:border-slate-300"
              }`}
            >
              {i === 0 ? "Objection line" : i === 1 ? "Hesitation line" : "Executive line"}
            </button>
          ))}
        </div>

        <div className="mt-5 grid gap-3 lg:grid-cols-2" data-testid="voice-cast-list">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-28 animate-pulse rounded-lg bg-secondary" />
              ))
            : (data ?? []).map((v) => (
                <div
                  key={v.character}
                  className="rounded-lg border border-border bg-card p-4"
                  data-testid={`voice-cast-${v.character.replace(/\s+/g, "-").toLowerCase()}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-heading text-[15.5px] font-bold">{v.character}</div>
                      <div className="text-[12.5px] text-muted-foreground">{v.role}</div>
                    </div>
                    <span
                      className={`flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-semibold ${
                        v.verified
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-red-50 text-red-700"
                      }`}
                      data-testid={`voice-status-${v.character.replace(/\s+/g, "-").toLowerCase()}`}
                    >
                      {v.verified ? (
                        <CheckCircle2 className="size-3.5" />
                      ) : (
                        <XCircle className="size-3.5" />
                      )}
                      {v.verified ? `${v.voice_label} loaded` : v.detail}
                    </span>
                  </div>
                  <p className="mt-2 text-[12.5px] leading-snug text-muted-foreground">
                    {v.style_note}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!v.verified || playing === v.character}
                      onClick={() => preview(v.character)}
                      data-testid={`voice-preview-${v.character.replace(/\s+/g, "-").toLowerCase()}`}
                      className="font-semibold"
                    >
                      {playing === v.character ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        <Play className="size-3.5" />
                      )}
                      Play preview
                    </Button>
                    <span className="font-mono text-[11.5px] text-muted-foreground">
                      stability {v.stability} · similarity {v.similarity_boost} · speed {v.speed}
                    </span>
                  </div>
                </div>
              ))}
        </div>
      </div>
    </AppShell>
  );
}
