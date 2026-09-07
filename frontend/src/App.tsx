import { Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import Training from "@/pages/Training";
import SimulationPage from "@/pages/Simulation";
import Scorecard from "@/pages/Scorecard";
import Progress from "@/pages/Progress";
import History from "@/pages/History";
import Profile from "@/pages/Profile";
import SkillModule from "@/pages/SkillModule";
import PracticeBusiness from "@/pages/PracticeBusiness";
import BusinessSetup from "@/pages/BusinessSetup";
import Team from "@/pages/Team";
import VoiceCast from "@/pages/VoiceCast";
import SampleReport from "@/pages/SampleReport";
import SessionBoundary from '@/components/SessionBoundary';
import EvidencePage from '@/pages/Evidence';
import GoogleCallback from '@/pages/GoogleCallback';
import Privacy from '@/pages/Privacy';
import Terms from '@/pages/Terms';
import Data from '@/pages/Data';

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  const location = useLocation();
  const state = new URLSearchParams(location.search).get('google_state');
  const fragment = new URLSearchParams(location.hash.replace(/^#/, ''));
  // Handle managed auth BEFORE SessionBoundary can check an old/absent session.
  if (fragment.has('session_id') || (location.pathname === '/dashboard' && state)) {
    return <GoogleCallback state={state} sessionId={fragment.get('session_id')} />;
  }
  return (
    <>
      <SessionBoundary><Routes>
        <Route path="/" element={<Landing />} />
        <Route path='/privacy' element={<Privacy />} />
        <Route path='/terms' element={<Terms />} />
        <Route path='/data' element={<Data />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/training" element={<Training />} />
        <Route path="/simulation/:id" element={<SimulationPage />} />
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
      </Routes></SessionBoundary>
      <Toaster position="top-right" richColors />
    </>
  );
}
