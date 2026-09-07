import { lazy, Suspense } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
const Landing = lazy(() => import("@/pages/Landing"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Training = lazy(() => import("@/pages/Training"));
const SimulationPage = lazy(() => import("@/pages/Simulation"));
const Scorecard = lazy(() => import("@/pages/Scorecard"));
const Progress = lazy(() => import("@/pages/Progress"));
const History = lazy(() => import("@/pages/History"));
const Profile = lazy(() => import("@/pages/Profile"));
const SkillModule = lazy(() => import("@/pages/SkillModule"));
const PracticeBusiness = lazy(() => import("@/pages/PracticeBusiness"));
const BusinessSetup = lazy(() => import("@/pages/BusinessSetup"));
const Team = lazy(() => import("@/pages/Team"));
const VoiceCast = lazy(() => import("@/pages/VoiceCast"));
const SampleReport = lazy(() => import("@/pages/SampleReport"));
import SessionBoundary from '@/components/SessionBoundary';
const EvidencePage = lazy(() => import("@/pages/Evidence"));
const GoogleCallback = lazy(() => import("@/pages/GoogleCallback"));
const Privacy = lazy(() => import("@/pages/Privacy"));
const Terms = lazy(() => import("@/pages/Terms"));
const Data = lazy(() => import("@/pages/Data"));

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  const location = useLocation();
  const state = new URLSearchParams(location.search).get('google_state');
  const fragment = new URLSearchParams(location.hash.replace(/^#/, ''));
  // Handle managed auth BEFORE SessionBoundary can check an old/absent session.
  if (fragment.has('session_id') || (location.pathname === '/dashboard' && state)) {
    return <Suspense fallback={<p role="status">Loading sign-in…</p>}><GoogleCallback state={state} sessionId={fragment.get('session_id')} /></Suspense>;
  }
  return (
    <>
      <SessionBoundary><Suspense fallback={<p className="p-8" role="status">Loading…</p>}><Routes>
        <Route path="/" element={<Landing />} />
        <Route path='/privacy' element={<Privacy />} />
        <Route path='/terms' element={<Terms />} />
        <Route path='/data' element={<Data />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/training" element={<Training />} />
        <Route path="/simulation/:id" element={<SimulationPage key={location.pathname} />} />
        <Route path="/scorecard/:id" element={<Scorecard />} />
        <Route path="/learn/:exerciseId" element={<SkillModule />} />
        <Route path="/practice-business" element={<PracticeBusiness />} />
        <Route path="/practice-business/setup" element={<BusinessSetup />} />
        <Route path="/practice-business/setup/:profileId" element={<BusinessSetup />} />
        <Route path="/team" element={<Team />} />
        <Route path="/voice-cast" element={<VoiceCast />} />
        <Route path="/sample-report" element={<SampleReport />} />
        <Route path='/owner/evidence' element={<EvidencePage />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Landing />} />
      </Routes></Suspense></SessionBoundary>
      <Toaster position="top-right" richColors />
    </>
  );
}
