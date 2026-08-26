import { useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  CheckCircle2,
  Lightbulb,
  Loader2,
  MessageSquareQuote,
  RotateCcw,
  Target,
  TriangleAlert,
} from "lucide-react";
import { apiGet } from "@/lib/api";
import { formatDuration, getUserId, tagMeta } from "@/lib/profile";
import type { Simulation } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { ScoreRing, SkillBar } from "@/components/Metrics";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export default function Scorecard() {
  const { id = "" } = useParams();
  const userId = getUserId();
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const { data: sim, isLoading, isError } = useQuery({
    queryKey: ["simulation", id],
    queryFn: () => apiGet<Simulation>(`/simulations/${id}`),
    retry: false,
  });

  const evaluation = sim?.evaluation ?? null;
  const momentsByTurn = useMemo(() => {
    const map = new Map<number, { tag: string; explanation: string }[]>();
    (evaluation?.moments ?? []).forEach((m) => {
      const list = map.get(m.turn_index) ?? [];
      list.push({ tag: m.tag, explanation: m.explanation });
      map.set(m.turn_index, list);
    });
    return map;
  }, [evaluation]);

  if (!userId) return <Navigate to="/" replace />;

  if (isLoading) {
    return (
      <AppShell>
        <div className="grid place-items-center py-24" data-testid="scorecard-loading">
          <Loader2 className="size-6 animate-spin text-primary" />
        </div>
      </AppShell>
    );
  }

  if (isError || !sim) {
    return (
      <AppShell>
        <div className="py-16 text-center" data-testid="scorecard-error">
          <h1 className="font-heading text-[22px] font-bold">Scorecard unavailable</h1>
          <p className="mt-2 text-[13.5px] text-muted-foreground">
            We couldn't load this debrief. Your other sessions are in History.
          </p>
          <Link to="/history" className={cn(buttonVariants({ variant: "outline" }), "mt-5")}>
            Go to history
          </Link>
        </div>
      </AppShell>
    );
  }

  const m = evaluation?.metrics;
  const talkData = m
    ? [
        { name: "You talking", value: m.talk_ratio },
        { name: "Prospect talking", value: Math.max(0, 100 - m.talk_ratio) },
      ]
    : [];
  const questionData = m
    ? [
        { name: "Open", value: m.open_questions },
        { name: "Closed", value: m.closed_questions },
      ]
    : [];

  const filteredMoments = (evaluation?.moments ?? []).filter(
    (mo) => !tagFilter || mo.tag === tagFilter,
  );
  const tagsPresent = Array.from(new Set((evaluation?.moments ?? []).map((mo) => mo.tag)));

  return (
    <AppShell>
      <div data-testid="scorecard-page">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[12.5px] text-muted-foreground">
              <Badge variant="secondary">{sim.exercise_name}</Badge>
              <span>
                Level {sim.difficulty} · {sim.difficulty_name}
              </span>
              <span>·</span>
              <span>{formatDuration(sim.duration_seconds)}</span>
              <span>·</span>
              <span>{sim.transcript.length} turns</span>
            </div>
            <h1 className="mt-2 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              Call debrief · {sim.scenario.prospect_name}
            </h1>
            <p className="mt-1 text-[14px] text-muted-foreground">
              {sim.scenario.prospect_role} at {sim.scenario.company}
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              to={
                sim.mode === "business"
                  ? "/practice-business"
                  : `/learn/${sim.exercise_id}?difficulty=${sim.difficulty}`
              }
              data-testid="scorecard-retry"
              className={cn(buttonVariants({ variant: "outline" }), "font-semibold")}
            >
              <RotateCcw className="size-4" />
              Retry this exercise
            </Link>
            {evaluation ? (
              <Link
                to={`/learn/${evaluation.recommended_exercise_id}?difficulty=${evaluation.recommended_difficulty}`}
                data-testid="scorecard-next-recommended"
                className={cn(buttonVariants(), "font-semibold")}
              >
                Practice what's next
                <ArrowRight className="size-4" />
              </Link>
            ) : null}
          </div>
        </div>

        {!evaluation ? (
          <div
            className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-5 text-[13.5px] text-amber-900"
            data-testid="scorecard-no-evaluation"
          >
            This call has no coaching analysis yet. End an active simulation to generate one.
          </div>
        ) : (
          <>
            <section className="mt-7 grid gap-6 rounded-xl border border-border bg-card p-6 lg:grid-cols-[auto_1fr]">
              <div className="flex flex-col items-center gap-3">
                <ScoreRing score={evaluation.overall_score} testid="overall-score" />
                <span className="text-[12px] text-muted-foreground">
                  +{sim.xp_awarded} XP earned
                </span>
              </div>
              <div>
                <h2 className="font-heading text-[20px] font-bold leading-snug" data-testid="scorecard-headline">
                  {evaluation.headline}
                </h2>
                <div
                  className={cn(
                    "mt-4 flex items-start gap-2.5 rounded-md p-3.5 text-[13.5px]",
                    evaluation.objective_met
                      ? "bg-emerald-50 text-emerald-900"
                      : "bg-red-50 text-red-900",
                  )}
                  data-testid="objective-outcome"
                >
                  <Target className="mt-0.5 size-4 shrink-0" />
                  <div>
                    <div className="font-semibold">
                      Objective {evaluation.objective_met ? "achieved" : "not achieved"}
                    </div>
                    <p className="mt-0.5 leading-relaxed">{evaluation.objective_note}</p>
                  </div>
                </div>
                {m ? (
                  <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      { k: "Talk ratio", v: `${m.talk_ratio}%`, t: "talk-ratio" },
                      { k: "Questions", v: String(m.question_count), t: "question-count" },
                      { k: "Filler words", v: String(m.filler_words), t: "filler-words" },
                      {
                        k: "Objections handled",
                        v: `${m.objections_handled}/${m.objection_count}`,
                        t: "objections",
                      },
                    ].map((s) => (
                      <div
                        key={s.k}
                        className="rounded-md bg-secondary p-3"
                        data-testid={`metric-${s.t}`}
                      >
                        <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                          {s.k}
                        </div>
                        <div className="mt-1 font-heading text-[19px] font-extrabold">{s.v}</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.15fr]">
              <section className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-heading text-[17px] font-bold">Competency scores</h2>
                <p className="text-[12.5px] text-muted-foreground">
                  Scored only where the category applied to this conversation.
                </p>
                <div className="mt-4 divide-y divide-border" data-testid="category-scores">
                  {evaluation.category_scores.map((c) => (
                    <SkillBar
                      key={c.category}
                      category={c.category}
                      score={c.score}
                      note={c.note}
                      testid={`category-${c.category.toLowerCase().replace(/\s+/g, "-")}`}
                    />
                  ))}
                </div>
              </section>

              <div className="space-y-6">
                <section className="rounded-xl border border-border bg-card p-5">
                  <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
                    <CheckCircle2 className="size-4 text-emerald-600" />
                    What you did well
                  </h2>
                  <div className="mt-4 space-y-3" data-testid="strengths-list">
                    {evaluation.strengths.map((s, i) => (
                      <div
                        key={i}
                        className="rounded-md border-l-4 border-emerald-500 bg-emerald-50/70 p-3.5"
                        data-testid={`strength-${i}`}
                      >
                        <div className="font-heading text-[14.5px] font-bold text-emerald-900">
                          {s.title}
                        </div>
                        <p className="mt-1 text-[13px] leading-relaxed text-emerald-950/80">
                          {s.detail}
                        </p>
                        {s.quote ? (
                          <p className="mt-2 font-mono text-[12px] italic text-emerald-800">
                            “{s.quote}”
                          </p>
                        ) : null}
                      </div>
                    ))}
                    {!evaluation.strengths.length ? (
                      <p className="text-[13px] text-muted-foreground">
                        Nothing stood out as a strength on this call — the coaching below is where to
                        start.
                      </p>
                    ) : null}
                  </div>
                </section>

                <section className="rounded-xl border border-border bg-card p-5">
                  <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
                    <TriangleAlert className="size-4 text-amber-600" />
                    Missed opportunities
                  </h2>
                  <div className="mt-4 space-y-3" data-testid="misses-list">
                    {evaluation.misses.map((s, i) => (
                      <div
                        key={i}
                        className="rounded-md border-l-4 border-amber-500 bg-amber-50/70 p-3.5"
                        data-testid={`miss-${i}`}
                      >
                        <div className="font-heading text-[14.5px] font-bold text-amber-900">
                          {s.title}
                        </div>
                        <p className="mt-1 text-[13px] leading-relaxed text-amber-950/80">
                          {s.detail}
                        </p>
                        {s.quote ? (
                          <p className="mt-2 font-mono text-[12px] italic text-amber-800">
                            “{s.quote}”
                          </p>
                        ) : null}
                        {s.better_approach ? (
                          <div className="mt-2.5 rounded-md bg-white p-2.5 text-[13px]">
                            <span className="font-semibold text-slate-900">Better approach: </span>
                            <span className="text-slate-700">{s.better_approach}</span>
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>

            <section className="mt-6 rounded-xl border border-border bg-[#0F172A] p-6 text-slate-100">
              <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
                <Lightbulb className="size-4 text-amber-400" />
                Coaching priorities
              </h2>
              <div className="mt-4 grid gap-4 md:grid-cols-3" data-testid="coaching-priorities">
                {evaluation.coaching_priorities.map((c, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
                    data-testid={`coaching-priority-${i}`}
                  >
                    <div className="font-mono text-[11px] text-slate-500">0{i + 1}</div>
                    <div className="mt-1.5 font-heading text-[16px] font-bold">{c.skill}</div>
                    <p className="mt-2 text-[13px] leading-relaxed text-slate-300">{c.why}</p>
                    <p className="mt-3 border-t border-slate-800 pt-3 text-[12.5px] text-sky-300">
                      Drill: {c.drill}
                    </p>
                  </div>
                ))}
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-800 pt-5">
                <p className="text-[13.5px] text-slate-300">{evaluation.recommended_reason}</p>
                <div className="ml-auto flex flex-wrap gap-2">
                  <Link
                    to={`/learn/${sim.exercise_id}?difficulty=${sim.difficulty}`}
                    className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 px-3.5 py-2 text-[13px] font-semibold text-slate-200"
                    data-testid="coaching-review-training"
                  >
                    Re-read the training
                  </Link>
                  <Link
                    to={`/learn/${evaluation.recommended_exercise_id}?difficulty=${evaluation.recommended_difficulty}`}
                    className="inline-flex items-center gap-1.5 rounded-md bg-white px-3.5 py-2 text-[13px] font-semibold text-[#0F172A]"
                    data-testid="coaching-next-exercise"
                  >
                    Practice this next
                    <ArrowRight className="size-4" />
                  </Link>
                </div>
              </div>
            </section>

            <Tabs defaultValue="transcript" className="mt-6">
              <TabsList data-testid="review-tabs">
                <TabsTrigger value="transcript" data-testid="tab-transcript">
                  Conversation review
                </TabsTrigger>
                <TabsTrigger value="analytics" data-testid="tab-analytics">
                  Communication analytics
                </TabsTrigger>
                <TabsTrigger value="intel" data-testid="tab-intel">
                  What was hidden
                </TabsTrigger>
              </TabsList>

              <TabsContent value="transcript">
                <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
                  <section className="rounded-xl border border-border bg-card p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setTagFilter(null)}
                        data-testid="moment-filter-all"
                        className={cn(
                          "rounded-full px-3 py-1 text-[12px] font-semibold",
                          !tagFilter ? "bg-[#0F172A] text-white" : "bg-secondary text-slate-600",
                        )}
                      >
                        All moments
                      </button>
                      {tagsPresent.map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setTagFilter(t)}
                          data-testid={`moment-filter-${t}`}
                          className={cn(
                            "rounded-full px-3 py-1 text-[12px] font-semibold",
                            tagFilter === t ? "bg-[#0F172A] text-white" : tagMeta(t).className,
                          )}
                        >
                          {tagMeta(t).label}
                        </button>
                      ))}
                    </div>

                    <div className="mt-5 space-y-3" data-testid="transcript-review">
                      {sim.transcript.map((t, i) => {
                        const tags = momentsByTurn.get(i) ?? [];
                        if (tagFilter && !tags.some((x) => x.tag === tagFilter)) return null;
                        return (
                          <div key={i} data-testid={`transcript-turn-${i}`}>
                            <div
                              className={cn(
                                "rounded-lg p-3.5 text-[13.5px] leading-relaxed",
                                t.speaker === "prospect"
                                  ? "bg-secondary"
                                  : "border border-border bg-card",
                              )}
                            >
                              <span className="mb-1 block text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                                {t.speaker === "prospect" ? sim.scenario.prospect_name : "You"}
                              </span>
                              {t.text}
                            </div>
                            {tags.map((tag, j) => (
                              <div
                                key={j}
                                className="mt-1.5 ml-4 rounded-md border-l-2 border-slate-300 bg-white p-3"
                                data-testid={`moment-${i}-${j}`}
                              >
                                <span
                                  className={cn(
                                    "inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold",
                                    tagMeta(tag.tag).className,
                                  )}
                                >
                                  {tagMeta(tag.tag).label}
                                </span>
                                <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
                                  {tag.explanation}
                                </p>
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  </section>

                  <aside className="rounded-xl border border-border bg-card p-5">
                    <h3 className="flex items-center gap-2 font-heading text-[15px] font-bold">
                      <MessageSquareQuote className="size-4 text-primary" />
                      Tagged moments
                    </h3>
                    <div className="mt-4 space-y-3" data-testid="moments-list">
                      {filteredMoments.map((mo, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setTagFilter(mo.tag)}
                          className="w-full rounded-md bg-secondary p-3 text-left"
                          data-testid={`moment-summary-${i}`}
                        >
                          <span
                            className={cn(
                              "inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold",
                              tagMeta(mo.tag).className,
                            )}
                          >
                            {tagMeta(mo.tag).label}
                          </span>
                          <p className="mt-1.5 text-[12.5px] leading-snug text-muted-foreground">
                            {mo.explanation}
                          </p>
                        </button>
                      ))}
                      {!filteredMoments.length ? (
                        <p className="text-[13px] text-muted-foreground">
                          No tagged moments for this filter.
                        </p>
                      ) : null}
                    </div>
                  </aside>
                </div>
              </TabsContent>

              <TabsContent value="analytics">
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  <section className="rounded-xl border border-border bg-card p-5">
                    <h3 className="font-heading text-[15px] font-bold">Talk vs listen</h3>
                    <div className="h-[210px]" data-testid="talk-ratio-chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={talkData}
                            dataKey="value"
                            innerRadius={52}
                            outerRadius={78}
                            paddingAngle={2}
                          >
                            <Cell fill="#2563EB" />
                            <Cell fill="#CBD5E1" />
                          </Pie>
                          <Tooltip formatter={(v) => `${String(v)}%`} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-[12.5px] text-muted-foreground">
                      You spoke {m?.talk_ratio ?? 0}% of the words. In discovery, strong reps usually
                      sit between 30% and 45%.
                    </p>
                  </section>

                  <section className="rounded-xl border border-border bg-card p-5">
                    <h3 className="font-heading text-[15px] font-bold">Question mix</h3>
                    <div className="h-[210px]" data-testid="question-mix-chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={questionData} margin={{ left: -20, top: 12 }}>
                          <XAxis
                            dataKey="name"
                            tick={{ fontSize: 12, fill: "#64748B" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fontSize: 12, fill: "#64748B" }}
                            axisLine={false}
                            tickLine={false}
                            allowDecimals={false}
                          />
                          <Tooltip />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            <Cell fill="#16A34A" />
                            <Cell fill="#94A3B8" />
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-[12.5px] text-muted-foreground">
                      {m?.question_count ?? 0} questions total. Open questions create discovery;
                      closed ones confirm.
                    </p>
                  </section>

                  <section className="rounded-xl border border-border bg-card p-5">
                    <h3 className="font-heading text-[15px] font-bold">Delivery</h3>
                    <div className="mt-4 space-y-3 text-[13px]" data-testid="delivery-metrics">
                      {[
                        { k: "Average response length", v: `${m?.avg_response_words ?? 0} words` },
                        { k: "Longest monologue", v: `${m?.longest_monologue_words ?? 0} words` },
                        { k: "Filler words", v: String(m?.filler_words ?? 0) },
                        {
                          k: "Objections handled",
                          v: `${m?.objections_handled ?? 0} of ${m?.objection_count ?? 0}`,
                        },
                      ].map((row) => (
                        <div
                          key={row.k}
                          className="flex items-center justify-between border-b border-border pb-2"
                        >
                          <span className="text-muted-foreground">{row.k}</span>
                          <span className="font-mono font-semibold">{row.v}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              </TabsContent>

              <TabsContent value="intel">
                <section className="rounded-xl border border-border bg-card p-6">
                  <h3 className="font-heading text-[17px] font-bold">
                    What {sim.scenario.prospect_name} knew and you had to earn
                  </h3>
                  <p className="mt-2 text-[13px] text-muted-foreground">
                    Hidden during the call. Compare it against what you actually uncovered.
                  </p>
                  <p
                    className="mt-4 rounded-md bg-secondary p-4 text-[13.5px] leading-relaxed"
                    data-testid="hidden-intel"
                  >
                    {sim.scenario.hidden ?? "Hidden intel is revealed once the call is graded."}
                  </p>
                  {sim.scenario.personality ? (
                    <p className="mt-3 text-[13px] text-muted-foreground">
                      Prospect personality: {sim.scenario.personality}
                    </p>
                  ) : null}
                  <div className="mt-5 flex flex-wrap gap-2">
                    {sim.scenario.objections.map((o) => (
                      <Badge key={o} variant="outline" className="text-[11.5px]">
                        {o}
                      </Badge>
                    ))}
                  </div>
                </section>
              </TabsContent>
            </Tabs>

            <div className="mt-8 flex flex-wrap justify-center gap-3 border-t border-border pt-6">
              <Link
                to={`/learn/${sim.exercise_id}?difficulty=${Math.min(5, sim.difficulty + 1)}`}
                className={cn(buttonVariants({ variant: "outline" }))}
                data-testid="scorecard-harder"
              >
                Try one level harder
              </Link>
              <Link to="/dashboard" className={cn(buttonVariants({ variant: "ghost" }))} data-testid="scorecard-dashboard">
                Back to dashboard
              </Link>
              <Button
                variant="secondary"
                onClick={() => window.print()}
                data-testid="scorecard-export"
              >
                Export debrief
              </Button>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
