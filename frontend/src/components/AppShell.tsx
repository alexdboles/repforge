import { useCurrentUser } from "@/lib/use-current-user";
import { Link, useLocation } from "react-router-dom";
import { Flame, Headphones, Zap } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import PrivacyLinks from './PrivacyLinks';

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/training", label: "Training" },
  { to: "/practice-business", label: "My Business" },
  { to: "/progress", label: "Progress" },
  { to: "/team", label: "Team" },
  { to: "/history", label: "History" },
  { to: "/profile", label: "Profile" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { data: user } = useCurrentUser();

  return (
    <div className="min-h-screen bg-background" data-testid="app-shell">
      <header className="sticky top-0 z-40 border-b border-border bg-white/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-6 px-5 sm:px-8">
          <Link to="/dashboard" className="flex items-center gap-2.5" data-testid="brand-link">
            <span className="grid size-8 place-items-center rounded-md bg-[#0F172A] text-white">
              <Headphones className="size-4" />
            </span>
            <span className="font-heading text-[17px] font-extrabold tracking-tight">
              RepForge
            </span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex" data-testid="primary-nav">
            {NAV.map((item) => {
              const active = pathname.startsWith(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-[14px] font-medium transition-colors",
                    active
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            {user?.is_admin ? <Link to='/owner/evidence' data-testid='owner-evidence-link' className='text-xs font-semibold text-primary'>Owner evidence</Link> : null}
            {user ? (
              <div className="hidden items-center gap-3 sm:flex" data-testid="shell-stats">
                <span className="flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-1 text-[12px] font-semibold text-slate-700">
                  <Zap className="size-3.5 text-amber-600" />
                  L{user.level} · {user.xp} XP
                </span>
                <span className="flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-1 text-[12px] font-semibold text-slate-700">
                  <Flame className="size-3.5 text-orange-600" />
                  {user.streak}d
                </span>
              </div>
            ) : null}
            <Link
              to="/training"
              data-testid="shell-start-simulation"
              className={cn(buttonVariants({ size: "sm" }), "font-semibold")}
            >
              Start Simulation
            </Link>
          </div>
        </div>

        <nav
          className="flex gap-1 overflow-x-auto border-t border-border px-4 py-2 md:hidden"
          data-testid="mobile-nav"
        >
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              data-testid={`mobile-nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
              className={cn(
                "shrink-0 rounded-md px-3 py-1.5 text-[13px] font-medium",
                pathname.startsWith(item.to)
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-[1400px] px-5 py-8 sm:px-8">{children}</main>

      <footer className="border-t border-border py-6 text-center text-[12px] text-muted-foreground">
        <p data-testid='shell-footer-copy'>RepForge · Practice the Conversation Before It Counts. · AI voice powered by ElevenLabs</p>
        <div className='mt-4 flex justify-center'><PrivacyLinks prefix='shell-footer' /></div>
      </footer>
    </div>
  );
}
