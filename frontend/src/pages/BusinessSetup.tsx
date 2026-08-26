import { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, Loader2, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import { getUserId } from "@/lib/profile";
import type { SalesProfile, SalesProfileInput } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const BLANK: SalesProfileInput = {
  label: "",
  company: "",
  industry: "",
  product: "",
  product_description: "",
  problems_solved: "",
  benefits: "",
  differentiators: "",
  customer_type: "Small businesses",
  customer_industries: "",
  customer_titles: "",
  ideal_customer: "",
  call_goal: "Book a meeting",
  sales_cycle: "",
  pricing: "",
  competitors: "",
  competitor_advantages: "",
  our_advantages: "",
  common_objections: [],
  methodology: "No formal methodology",
  extra_context: "",
};

const CUSTOMER_TYPES = ["Consumers", "Small businesses", "Mid-market", "Enterprise businesses"];
const CALL_GOALS = [
  "Book a meeting",
  "Make a sale",
  "Qualify the prospect",
  "Generate interest",
  "Get a referral",
  "Advance an opportunity",
];
const METHODOLOGIES = [
  "No formal methodology",
  "Consultative Selling",
  "Sandler-inspired",
  "SPIN",
  "Challenger",
  "MEDDIC",
  "Company-specific methodology",
];
const OBJECTION_SUGGESTIONS = [
  "We already use another provider",
  "That's too expensive",
  "I'm not interested",
  "Send me an email",
  "We don't have budget",
  "I'm happy with our current solution",
  "Call me next quarter",
  "I need to talk to my boss",
];

const STEPS = [
  { title: "Company", hint: "Who you work for" },
  { title: "Product", hint: "What you sell and what it fixes" },
  { title: "Customer", hint: "Who you sell to" },
  { title: "Sales process", hint: "Goals, cycle and pricing" },
  { title: "Competition", hint: "Who else is in the deal" },
  { title: "Objections", hint: "What you actually hear" },
  { title: "Method & context", hint: "Anything else the AI should know" },
];

export default function BusinessSetup() {
  const userId = getUserId();
  const { profileId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<SalesProfileInput>(BLANK);
  const [objection, setObjection] = useState("");
  const [loaded, setLoaded] = useState(false);

  const { data: existing } = useQuery({
    queryKey: ["sales-profile", profileId],
    queryFn: () => apiGet<SalesProfile>(`/sales-profiles/${profileId}`),
    enabled: Boolean(profileId),
    retry: false,
  });

  useEffect(() => {
    if (existing && !loaded) {
      const { id: _id, user_id: _u, created_at: _c, ...rest } = existing;
      setForm(rest);
      setLoaded(true);
    }
  }, [existing, loaded]);

  const save = useMutation({
    mutationFn: () =>
      profileId
        ? apiPatch<SalesProfile>(`/sales-profiles/${profileId}`, form)
        : apiPost<SalesProfile>(`/users/${userId}/sales-profiles`, form),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["sales-profiles", userId] });
      toast.success(profileId ? "Sales profile updated" : "Sales profile saved");
      navigate(`/practice-business?profile=${p.id}`);
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof (err.body as { detail?: string })?.detail === "string"
          ? (err.body as { detail: string }).detail
          : "Could not save the profile.";
      toast.error(detail);
    },
  });

  // Only recompute the suggestion chips when the rep's own objection list changes.
  const remainingSuggestions = useMemo(
    () => OBJECTION_SUGGESTIONS.filter((o) => !form.common_objections.includes(o)),
    [form.common_objections],
  );

  if (!userId) return <Navigate to="/" replace />;

  const set = <K extends keyof SalesProfileInput>(key: K, value: SalesProfileInput[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const addObjection = (text: string) => {
    const clean = text.trim();
    if (!clean || form.common_objections.includes(clean)) return;
    set("common_objections", [...form.common_objections, clean]);
    setObjection("");
  };

  const canAdvance = () => {
    if (step === 0) return form.company.trim().length > 1;
    if (step === 1) return form.product.trim().length > 1;
    return true;
  };

  const next = () => {
    if (!canAdvance()) {
      toast.error(step === 0 ? "Company name is required" : "Product name is required");
      return;
    }
    if (step === STEPS.length - 1) {
      const payload = { ...form, label: form.label.trim() || `${form.company} — ${form.product}` };
      setForm(payload);
      save.mutate();
      return;
    }
    setStep((s) => s + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-[860px]" data-testid="business-setup-page">
        <Badge variant="secondary">Practice My Business</Badge>
        <h1 className="mt-2 font-heading text-[30px] font-extrabold tracking-[-0.02em]">
          {profileId ? "Edit your sales profile" : "Tell us about your sales job"}
        </h1>
        <p className="mt-1.5 text-[14px] text-muted-foreground">
          Answer this once. Every future custom scenario is generated from it — company, product,
          buyers, pricing, competitors and the objections you actually hear.
        </p>

        <div className="mt-7 flex flex-wrap gap-1.5" data-testid="setup-progress">
          {STEPS.map((s, i) => (
            <button
              key={s.title}
              type="button"
              onClick={() => i <= step && setStep(i)}
              data-testid={`setup-step-${i}`}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors",
                i === step
                  ? "bg-[#0F172A] text-white"
                  : i < step
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-secondary text-muted-foreground",
              )}
            >
              {i < step ? <Check className="size-3" /> : null}
              {s.title}
            </button>
          ))}
        </div>

        <div className="mt-6 rounded-xl border border-border bg-card p-6">
          <h2 className="font-heading text-[19px] font-bold">{STEPS[step].title}</h2>
          <p className="text-[13px] text-muted-foreground">{STEPS[step].hint}</p>

          <div className="mt-5 space-y-4">
            {step === 0 ? (
              <>
                <Field label="What company do you work for?" testid="field-company">
                  <Input
                    value={form.company}
                    onChange={(e) => set("company", e.target.value)}
                    placeholder="Northwind CRM"
                    data-testid="input-company"
                  />
                </Field>
                <Field label="What industry are you in?" testid="field-industry">
                  <Input
                    value={form.industry}
                    onChange={(e) => set("industry", e.target.value)}
                    placeholder="B2B SaaS"
                    data-testid="input-industry"
                  />
                </Field>
                <Field label="Name this profile (optional)" testid="field-label">
                  <Input
                    value={form.label}
                    onChange={(e) => set("label", e.target.value)}
                    placeholder="My day job"
                    data-testid="input-label"
                  />
                </Field>
              </>
            ) : null}

            {step === 1 ? (
              <>
                <Field label="What product or service do you sell?" testid="field-product">
                  <Input
                    value={form.product}
                    onChange={(e) => set("product", e.target.value)}
                    placeholder="Northwind CRM"
                    data-testid="input-product"
                  />
                </Field>
                <Field label="Describe what it does" testid="field-product-description">
                  <Textarea
                    value={form.product_description}
                    onChange={(e) => set("product_description", e.target.value)}
                    rows={3}
                    placeholder="A CRM built for small service businesses — quotes, follow-ups and job scheduling in one place."
                    data-testid="input-product-description"
                  />
                </Field>
                <Field label="What problems does it solve?" testid="field-problems">
                  <Textarea
                    value={form.problems_solved}
                    onChange={(e) => set("problems_solved", e.target.value)}
                    rows={3}
                    placeholder="Lost follow-ups, no pipeline visibility, quotes going cold."
                    data-testid="input-problems"
                  />
                </Field>
                <Field label="Primary benefits" testid="field-benefits">
                  <Textarea
                    value={form.benefits}
                    onChange={(e) => set("benefits", e.target.value)}
                    rows={2}
                    data-testid="input-benefits"
                  />
                </Field>
                <Field label="Strongest differentiators" testid="field-differentiators">
                  <Textarea
                    value={form.differentiators}
                    onChange={(e) => set("differentiators", e.target.value)}
                    rows={2}
                    placeholder="Live in a day, no consultants, phone support from real humans."
                    data-testid="input-differentiators"
                  />
                </Field>
              </>
            ) : null}

            {step === 2 ? (
              <>
                <Field label="Who do you normally sell to?" testid="field-customer-type">
                  <Select
                    value={form.customer_type}
                    onValueChange={(v: string) => set("customer_type", v)}
                  >
                    <SelectTrigger data-testid="select-customer-type">
                      <SelectValue>{(v) => String(v)}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {CUSTOMER_TYPES.map((c) => (
                        <SelectItem key={c} value={c} data-testid={`customer-type-${c}`}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="What industries?" testid="field-customer-industries">
                  <Input
                    value={form.customer_industries}
                    onChange={(e) => set("customer_industries", e.target.value)}
                    placeholder="Landscaping, trades, home services"
                    data-testid="input-customer-industries"
                  />
                </Field>
                <Field label="What job titles or personas?" testid="field-customer-titles">
                  <Input
                    value={form.customer_titles}
                    onChange={(e) => set("customer_titles", e.target.value)}
                    placeholder="Owner, Operations Manager"
                    data-testid="input-customer-titles"
                  />
                </Field>
                <Field label="What does your ideal customer look like?" testid="field-ideal">
                  <Textarea
                    value={form.ideal_customer}
                    onChange={(e) => set("ideal_customer", e.target.value)}
                    rows={2}
                    placeholder="15-50 person service business with field crews and no CRM."
                    data-testid="input-ideal"
                  />
                </Field>
              </>
            ) : null}

            {step === 3 ? (
              <>
                <Field label="Typical goal of your cold call" testid="field-call-goal">
                  <Select value={form.call_goal} onValueChange={(v: string) => set("call_goal", v)}>
                    <SelectTrigger data-testid="select-call-goal">
                      <SelectValue>{(v) => String(v)}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {CALL_GOALS.map((c) => (
                        <SelectItem key={c} value={c} data-testid={`call-goal-${c}`}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Typical sales cycle" testid="field-cycle">
                  <Input
                    value={form.sales_cycle}
                    onChange={(e) => set("sales_cycle", e.target.value)}
                    placeholder="3 weeks from first call to signature"
                    data-testid="input-cycle"
                  />
                </Field>
                <Field label="What does it normally cost?" testid="field-pricing">
                  <Textarea
                    value={form.pricing}
                    onChange={(e) => set("pricing", e.target.value)}
                    rows={2}
                    placeholder="$199/month for up to 10 users; Pro at $349/month adds scheduling."
                    data-testid="input-pricing"
                  />
                </Field>
              </>
            ) : null}

            {step === 4 ? (
              <>
                <Field label="Main competitors" testid="field-competitors">
                  <Input
                    value={form.competitors}
                    onChange={(e) => set("competitors", e.target.value)}
                    placeholder="Competitor X ($120/mo), Competitor Y"
                    data-testid="input-competitors"
                  />
                </Field>
                <Field label="What advantages do they have?" testid="field-competitor-advantages">
                  <Textarea
                    value={form.competitor_advantages}
                    onChange={(e) => set("competitor_advantages", e.target.value)}
                    rows={2}
                    data-testid="input-competitor-advantages"
                  />
                </Field>
                <Field label="What advantages do you have?" testid="field-our-advantages">
                  <Textarea
                    value={form.our_advantages}
                    onChange={(e) => set("our_advantages", e.target.value)}
                    rows={2}
                    data-testid="input-our-advantages"
                  />
                </Field>
              </>
            ) : null}

            {step === 5 ? (
              <>
                <Field label="What objections do you commonly hear?" testid="field-objections">
                  <div className="flex gap-2">
                    <Input
                      value={objection}
                      onChange={(e) => setObjection(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addObjection(objection);
                        }
                      }}
                      placeholder="Type an objection and press Enter"
                      data-testid="input-objection"
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => addObjection(objection)}
                      data-testid="add-objection-button"
                    >
                      <Plus className="size-4" />
                      Add
                    </Button>
                  </div>
                </Field>
                <div className="flex flex-wrap gap-2" data-testid="objection-list">
                  {form.common_objections.map((o) => (
                    <span
                      key={o}
                      className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-[12.5px] font-medium"
                      data-testid={`objection-chip-${o}`}
                    >
                      {o}
                      <button
                        type="button"
                        onClick={() =>
                          set(
                            "common_objections",
                            form.common_objections.filter((x) => x !== o),
                          )
                        }
                        aria-label={`Remove ${o}`}
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="rounded-md bg-secondary/60 p-3.5">
                  <div className="text-[12px] font-semibold text-muted-foreground">
                    Common ones — tap to add
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {remainingSuggestions.map(
                      (o) => (
                        <button
                          key={o}
                          type="button"
                          onClick={() => addObjection(o)}
                          data-testid={`objection-suggestion-${o}`}
                          className="rounded-full border border-border bg-card px-3 py-1 text-[12.5px] hover:border-slate-300"
                        >
                          + {o}
                        </button>
                      ),
                    )}
                  </div>
                </div>
              </>
            ) : null}

            {step === 6 ? (
              <>
                <Field label="Does your team use a sales methodology?" testid="field-methodology">
                  <Select
                    value={form.methodology}
                    onValueChange={(v: string) => set("methodology", v)}
                  >
                    <SelectTrigger data-testid="select-methodology">
                      <SelectValue>{(v) => String(v)}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {METHODOLOGIES.map((m) => (
                        <SelectItem key={m} value={m} data-testid={`methodology-${m}`}>
                          {m}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field
                  label="Anything else the AI prospect should know about your market?"
                  testid="field-extra"
                >
                  <Textarea
                    value={form.extra_context}
                    onChange={(e) => set("extra_context", e.target.value)}
                    rows={4}
                    placeholder="Seasonal buying, referral-heavy market, gatekeepers screen every call…"
                    data-testid="input-extra"
                  />
                </Field>
              </>
            ) : null}
          </div>

          <div className="mt-7 flex items-center justify-between border-t border-border pt-5">
            <Button
              variant="ghost"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
              data-testid="setup-back"
            >
              <ArrowLeft className="size-4" />
              Back
            </Button>
            <Button onClick={next} disabled={save.isPending} data-testid="setup-next" className="font-semibold">
              {save.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving…
                </>
              ) : step === STEPS.length - 1 ? (
                "Save sales profile"
              ) : (
                <>
                  Continue
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Field({
  label,
  testid,
  children,
}: {
  label: string;
  testid: string;
  children: React.ReactNode;
}) {
  return (
    <div data-testid={testid}>
      <Label className="text-[13.5px]">{label}</Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}
