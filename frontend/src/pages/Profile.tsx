import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Award, Flame, LogOut, Trophy, Users, Zap } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { clearToken, clearUserId, formatDuration, getUserId } from "@/lib/profile";
import type { Dashboard as DashboardData, UserProfile } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { StatCard } from "@/components/Metrics";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const LEVELS: Record<string, string> = {
  New: "New to sales (0-1 years)",
  Developing: "Developing (1-3 years)",
  Experienced: "Experienced (3+ years)",
  Manager: "Sales manager / enablement",
};

export default function Profile() {
  const userId = getUserId();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => apiGet<UserProfile>(`/users/${userId}`),
    enabled: Boolean(userId),
    retry: false,
  });
  const { data: dash } = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => apiGet<DashboardData>(`/users/${userId}/dashboard`),
    enabled: Boolean(userId),
    retry: false,
  });

  const [name, setName] = useState("");
  const [experience, setExperience] = useState("New");
  const [org, setOrg] = useState("Personal");

  useEffect(() => {
    if (user) {
      setName(user.name);
      setExperience(user.experience_level);
      setOrg(user.org);
    }
  }, [user]);

  const save = useMutation({
    mutationFn: () =>
      apiPatch<UserProfile>(`/users/${userId}`, {
        name,
        experience_level: experience,
        org,
        role: user?.role ?? "Sales Professional",
      }),
    onSuccess: () => {
      toast.success("Profile updated");
      qc.invalidateQueries({ queryKey: ["user", userId] });
      qc.invalidateQueries({ queryKey: ["dashboard", userId] });
    },
    onError: () => toast.error("Could not save your profile"),
  });

  if (!userId) return <Navigate to="/" replace />;

  const nextLevelXp = Math.pow(user ? user.level : 1, 2) * 250;
  const progressPct = user ? Math.min(100, Math.round((user.xp / Math.max(1, nextLevelXp)) * 100)) : 0;

  return (
    <AppShell>
      <div data-testid="profile-page">
        <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">Profile</h1>
        <p className="mt-1.5 text-[14px] text-muted-foreground">
          Your training identity, progression and achievements.
        </p>

        <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_1.3fr]">
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading text-[17px] font-bold">Rep details</h2>
            <div className="mt-4 space-y-4">
              <div>
                <Label htmlFor="p-name">Name</Label>
                <Input
                  id="p-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1.5"
                  data-testid="profile-name-input"
                />
              </div>
              <div>
                <Label htmlFor="p-exp">Experience level</Label>
                <Select value={experience} onValueChange={(v: string) => setExperience(v)}>
                  <SelectTrigger id="p-exp" className="mt-1.5" data-testid="profile-experience-trigger">
                    <SelectValue>{(v) => LEVELS[v as string] ?? "Select"}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {Object.keys(LEVELS).map((k) => (
                      <SelectItem key={k} value={k} data-testid={`profile-experience-${k}`}>
                        {LEVELS[k]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="p-org">Organisation</Label>
                <Input
                  id="p-org"
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                  className="mt-1.5"
                  data-testid="profile-org-input"
                />
                <p className="mt-1.5 text-[12px] text-muted-foreground">
                  Reps sharing an organisation roll up into team reporting — the manager view is the
                  next stage of the roadmap.
                </p>
              </div>
              <Button
                onClick={() => save.mutate()}
                disabled={save.isPending}
                data-testid="profile-save-button"
                className="font-semibold"
              >
                {save.isPending ? "Saving…" : "Save profile"}
              </Button>
            </div>

            <div className="mt-6 border-t border-border pt-5">
              <Button
                variant="ghost"
                onClick={async () => {
                  // Server-side session teardown first, then clear local caches.
                  await apiPost("/auth/logout").catch(() => undefined);
                  clearUserId();
                  clearToken();
                  qc.clear();
                  navigate("/");
                }}
                data-testid="profile-logout-button"
                className="text-muted-foreground"
              >
                <LogOut className="size-4" />
                Sign out
              </Button>
            </div>
          </section>

          <div className="space-y-6">
            <section className="rounded-xl border border-border bg-[#0F172A] p-5 text-slate-100">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                    Training level
                  </div>
                  <div className="mt-1 font-heading text-[30px] font-extrabold">
                    Level {user?.level ?? 1}
                  </div>
                </div>
                <div className="flex gap-4 text-right">
                  <div>
                    <div className="flex items-center gap-1.5 text-[12px] text-slate-400">
                      <Zap className="size-3.5 text-amber-400" /> XP
                    </div>
                    <div className="font-heading text-[20px] font-bold" data-testid="profile-xp">
                      {user?.xp ?? 0}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 text-[12px] text-slate-400">
                      <Flame className="size-3.5 text-orange-400" /> Streak
                    </div>
                    <div className="font-heading text-[20px] font-bold" data-testid="profile-streak">
                      {user?.streak ?? 0}d
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-sky-400"
                  style={{ width: `${progressPct}%`, transition: "width 700ms ease-out" }}
                />
              </div>
              <p className="mt-2 text-[12px] text-slate-400">
                {nextLevelXp - (user?.xp ?? 0) > 0
                  ? `${nextLevelXp - (user?.xp ?? 0)} XP to Level ${(user?.level ?? 1) + 1}`
                  : "Next level unlocked on your next completed call"}
              </p>
            </section>

            <div className="grid gap-4 sm:grid-cols-3">
              <StatCard
                testid="profile-stat-reps"
                label="Reps"
                value={String(dash?.completed ?? 0)}
                hint={formatDuration(dash?.total_practice_seconds ?? 0)}
              />
              <StatCard
                testid="profile-stat-best"
                label="Personal best"
                value={dash?.personal_best ? String(dash.personal_best) : "—"}
              />
              <StatCard
                testid="profile-stat-tier"
                label="Tier unlocked"
                value={`L${dash?.unlocked_difficulty ?? 2}`}
              />
            </div>

            <section className="rounded-xl border border-border bg-card p-5">
              <h2 className="flex items-center gap-2 font-heading text-[17px] font-bold">
                <Trophy className="size-4 text-amber-600" />
                Achievements
              </h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2" data-testid="profile-badges">
                {(dash?.badges ?? []).map((b) => (
                  <div
                    key={b.id}
                    className={cn(
                      "flex items-start gap-3 rounded-lg border p-3",
                      b.earned ? "border-amber-200 bg-amber-50" : "border-border bg-secondary/40",
                    )}
                    data-testid={`badge-${b.id}`}
                  >
                    <Award
                      className={cn(
                        "mt-0.5 size-4 shrink-0",
                        b.earned ? "text-amber-600" : "text-slate-400",
                      )}
                    />
                    <div>
                      <div
                        className={cn(
                          "text-[13.5px] font-semibold",
                          b.earned ? "text-amber-900" : "text-muted-foreground",
                        )}
                      >
                        {b.name}
                      </div>
                      <p className="text-[12px] text-muted-foreground">{b.description}</p>
                    </div>
                  </div>
                ))}
                {!dash?.badges.length ? (
                  <p className="text-[13px] text-muted-foreground">
                    Achievements unlock as you complete simulations.
                  </p>
                ) : null}
              </div>
            </section>

            <section className="rounded-xl border border-dashed border-border bg-card p-5">
              <h2 className="flex items-center gap-2 font-heading text-[15px] font-bold">
                <Users className="size-4 text-primary" />
                Team & manager reporting
              </h2>
              <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                Every simulation, transcript and competency score is stored against your rep record
                and organisation, so manager dashboards, skill-gap reporting, assigned exercises and
                team leaderboards roll straight out of the existing data model. Not enabled in this
                individual-seller release.
              </p>
            </section>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
