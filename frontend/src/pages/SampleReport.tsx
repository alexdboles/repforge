import { Link, Navigate } from "react-router-dom";
import { useState } from "react";
import { ArrowRight, CheckCircle2, Lightbulb, RotateCcw, TriangleAlert, Volume2 } from "lucide-react";
import { toast } from "sonner";
import { getUserId } from "@/lib/profile";
import AppShell from "@/components/AppShell";
import { ScoreRing, SkillBar } from "@/components/Metrics";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Hand-authored demonstration data. Clearly labelled SAMPLE everywhere so it can
// never be mistaken for the signed-in rep's own performance.
const SKILLS = [
  { category: "Opening", score: 88, note: "Strong introduction and a clear reason for the conversation." },
  { category: "Rapport", score: 86, note: "Natural conversational tone without unnecessary small talk." },
  { category: "Active Listening", score: 91, note: "Responded directly to information the buyer volunteered." },
  { category: "Discovery", score: 72, note: "Identified the problem but did not explore its business impact." },
  { category: "Value Communication", score: 79, note: "Connected features to stated buyer needs." },
  { category: "Objection Handling", score: 64, note: "Defended pricing too quickly." },
  { category: "Closing / Next Step", score: 76, note: "Set a reasonable follow-up but did not confirm stakeholders." },
];

const METRICS = [
  { k: "Talk / listen", v: "42% / 58%" },
  { k: "Questions asked", v: "9" },
  { k: "Open-ended questions", v: "6" },
  { k: "Follow-up questions", v: "4" },
  { k: "Interruptions", v: "1" },
  { k: "Longest monologue", v: "38s" },
  { k: "Buying signals", v: "2" },
  { k: "Missed buying signals", v: "1" },
];

const TIMELINE = [
  { at: "00:00", label: "Opening", tone: "strong" },
  { at: "00:48", label: "Permission / rapport", tone: "strong" },
  { at: "01:31", label: "Discovery begins", tone: "strong" },
  { at: "02:42", label: "Pain identified", tone: "strong" },
  { at: "03:08", label: "Premature pitch", tone: "coaching" },
  { at: "03:42", label: "Price objection", tone: "weak" },
  { at: "04:16", label: "Missed vocal cue", tone: "weak" },
  { at: "06:51", label: "Next step established", tone: "strong" },
] as const;

const STRENGTHS = [
  "Natural opening",
  "Strong listening ratio",
  "Good follow-up questions",
  "Clear value statement",
  "Secured a next step",
];

const PRIORITIES = [
  { skill: "Objection Handling", why: "Don't immediately defend price — find out what it is being compared against." },
  { skill: "Discovery Depth", why: "Explore business impact before presenting any solution." },
  { skill: "Vocal Cue Recognition", why: "Check hesitation instead of assuming agreement." },
];

const toneStyle = {
  strong: "border-emerald-500 bg-emerald-50 text-emerald-900",
  coaching: "border-amber-500 bg-amber-50 text-amber-900",
  weak: "border-red-500 bg-red-50 text-red-900",
} as const;

export default function SampleReport() {
  const userId = getUserId();
  const [selected, setSelected] = useState<string>("03:42");
  if (!userId) return <Navigate to="/" replace />;

  return (
    <AppShell>
      <div data-testid="sample-report-page">
        <span
          className="inline-flex items-center rounded-full bg-[#0F172A] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white"
          data-testid="sample-report-badge"
        >
          Sample data · not your performance
        </span>
        <h1 className="mt-3 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
          RepForge Coaching Report · Sarah Chen
        </h1>
        <p className="mt-1.5 max-w-2xl text-[14px] text-muted-foreground">
          Discovery Meeting · Rep: Jordan Miller · Buyer: Sarah Chen, VP of Operations, Meridian
          Logistics · Developing · 7:42
        </p>

        <div className="mt-6 grid gap-6 lg:grid-cols-[auto_1fr]">
          <section className="flex flex-col items-center rounded-xl border border-border bg-card p-6">
            <ScoreRing score={78} label="Readiness" testid="sample-readiness" />
            <span className="mt-2 rounded-full bg-secondary px-3 py-1 text-[12px] font-semibold">
              Developing
            </span>
            <p className="mt-3 max-w-[210px] text-center text-[12.5px] text-muted-foreground">
              Strong listening and rapport. Needs deeper discovery before presenting value.
            </p>
          </section>

          <section
            className="rounded-xl border border-border bg-[#0F172A] p-6 text-slate-100"
            data-testid="sample-one-thing"
          >
            <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-300">
              <Lightbulb className="size-3.5" />
              Coach's one thing
            </span>
            <h2 className="mt-3 font-heading text-[24px] font-extrabold leading-snug">
              Ask one more question before you pitch.
            </h2>
            <p className="mt-3 max-w-2xl text-[14px] leading-relaxed text-slate-300">
              You correctly identified Sarah's operational problem, but moved into your solution
              before understanding what it was costing the business.
            </p>
          </section>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading text-[17px] font-bold">Skill breakdown</h2>
            <div className="mt-4 space-y-3" data-testid="sample-skill-breakdown">
              {SKILLS.map((s) => (
                <div key={s.category}>
                  <SkillBar category={s.category} score={s.score} />
                  <p className="mt-1 text-[12.5px] text-muted-foreground">{s.note}</p>
                </div>
              ))}
            </div>
          </section>

          <div className="space-y-6">
            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="font-heading text-[17px] font-bold">Conversation metrics</h2>
              <p className="mt-1 text-[12.5px] text-muted-foreground">
                Measured, not judged — these are counted from the call itself.
              </p>
              <dl className="mt-4 grid grid-cols-2 gap-3" data-testid="sample-metrics">
                {METRICS.map((m) => (
                  <div key={m.k} className="rounded-lg border border-border p-3">
                    <dt className="text-[11.5px] uppercase tracking-[0.12em] text-muted-foreground">
                      {m.k}
                    </dt>
                    <dd className="mt-1 font-heading text-[19px] font-extrabold">{m.v}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <section
              className="rounded-xl border border-sky-200 bg-sky-50 p-5"
              data-testid="sample-listening-iq"
            >
              <div className="flex items-baseline justify-between">
                <h2 className="font-heading text-[17px] font-bold">Listening IQ</h2>
                <span className="font-heading text-[24px] font-extrabold text-sky-800">86</span>
              </div>
              <p className="mt-2 text-[13px] leading-relaxed text-slate-700">
                You generally responded to what Sarah actually said rather than working through a
                predetermined script.
              </p>
              <div className="mt-3 rounded-lg bg-white p-3.5">
                <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red-700">
                  Missed vocal cue
                </span>
                <p className="mt-1.5 font-mono text-[13px] italic text-slate-800">
                  “Yeah… I guess that could work.”
                </p>
                <p className="mt-2 text-[13px] leading-relaxed text-slate-700">
                  Sarah verbally agreed, but her delivery showed hesitation. You kept presenting
                  instead of checking whether she had a concern.
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3 font-semibold"
                  onClick={() => toast.info("Audio replay is available on your own graded calls.")}
                  data-testid="sample-replay-cue"
                >
                  <Volume2 className="size-3.5" />
                  Replay moment
                </Button>
              </div>
            </section>
          </div>
        </div>

        <section className="mt-6 rounded-xl border border-border bg-card p-5">
          <h2 className="font-heading text-[17px] font-bold">Conversation timeline</h2>
          <div className="mt-4 flex flex-wrap gap-2" data-testid="sample-timeline">
            {TIMELINE.map((t) => (
              <button
                key={t.at}
                type="button"
                onClick={() => setSelected(t.at)}
                data-testid={`sample-timeline-${t.at.replace(":", "-")}`}
                className={cn(
                  "rounded-md border-l-4 px-3 py-2 text-left text-[12.5px] transition-colors",
                  toneStyle[t.tone],
                  selected === t.at && "ring-2 ring-slate-900/20",
                )}
              >
                <span className="font-mono text-[11px] opacity-70">{t.at}</span>
                <span className="ml-2 font-semibold">{t.label}</span>
              </button>
            ))}
          </div>

          {selected === "03:42" ? (
            <div
              className="mt-4 rounded-lg border-l-4 border-red-500 bg-red-50/70 p-4"
              data-testid="sample-coaching-moment"
            >
              <div className="flex items-center gap-2 font-heading text-[15px] font-bold text-red-900">
                <TriangleAlert className="size-4" />
                Price objection · 03:42
              </div>
              <p className="mt-2.5 text-[13px] text-slate-800">
                <span className="font-semibold">Sarah: </span>
                <span className="font-mono italic">
                  “Honestly, that sounds expensive compared with what we're already paying.”
                </span>
              </p>
              <p className="mt-1.5 text-[13px] text-slate-800">
                <span className="font-semibold">You: </span>
                <span className="font-mono italic">
                  “Our platform actually includes considerably more functionality…”
                </span>
              </p>
              <p className="mt-2.5 text-[13px] leading-relaxed text-slate-700">
                <span className="font-semibold">RepForge Coach: </span>
                You defended the product before finding out whether price was the real objection.
                A stronger response first establishes what Sarah is comparing the investment
                against.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  className="font-semibold"
                  onClick={() =>
                    toast.info(
                      "On your own calls, this drops you straight back into this moment: Sarah repeats the objection in her own voice and reacts to your new answer.",
                    )
                  }
                  data-testid="sample-retry-moment"
                >
                  <RotateCcw className="size-3.5" />
                  See how Retry That Moment works
                </Button>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-[13px] text-muted-foreground" data-testid="sample-timeline-hint">
              Select the 03:42 price objection to see a full coaching moment with Retry That Moment.
            </p>
          )}
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
              <CheckCircle2 className="size-4 text-emerald-600" />
              What went well
            </h2>
            <ul className="mt-3 space-y-2" data-testid="sample-strengths">
              {STRENGTHS.map((s) => (
                <li key={s} className="text-[13.5px] text-slate-700">
                  ✓ {s}
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading text-[17px] font-bold">Focus next</h2>
            <ol className="mt-3 space-y-3" data-testid="sample-priorities">
              {PRIORITIES.map((p, i) => (
                <li key={p.skill}>
                  <div className="font-heading text-[14.5px] font-bold">
                    {i + 1}. {p.skill}
                  </div>
                  <p className="text-[13px] text-muted-foreground">{p.why}</p>
                </li>
              ))}
            </ol>
          </section>
        </div>

        <section
          className="mt-6 flex flex-wrap items-center gap-5 rounded-xl border border-border bg-[#0F172A] p-6 text-slate-100"
          data-testid="sample-recommendation"
        >
          <div className="min-w-0 flex-1">
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              RepForge recommendation
            </span>
            <h2 className="mt-2 font-heading text-[20px] font-extrabold">
              Price objection drill · ~4 minutes
            </h2>
            <p className="mt-1.5 max-w-xl text-[13.5px] text-slate-400">
              Practise finding out what is actually behind a pricing objection before you respond.
            </p>
          </div>
          <Link
            to="/learn/objection-handling?difficulty=3"
            className={cn(buttonVariants({ size: "lg" }), "bg-slate-100 font-semibold text-slate-900 hover:bg-white")}
            data-testid="sample-start-drill"
          >
            Start recommended drill
            <ArrowRight className="size-4" />
          </Link>
        </section>
      </div>
    </AppShell>
  );
}
