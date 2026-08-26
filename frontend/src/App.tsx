import { Routes, Route } from "react-router-dom";
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

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/training" element={<Training />} />
        <Route path="/simulation/:id" element={<SimulationPage />} />
        <Route path="/scorecard/:id" element={<Scorecard />} />
        <Route path="/learn/:exerciseId" element={<SkillModule />} />
        <Route path="/practice-business" element={<PracticeBusiness />} />
        <Route path="/practice-business/setup" element={<BusinessSetup />} />
        <Route path="/practice-business/setup/:profileId" element={<BusinessSetup />} />
        <Route path="/team" element={<Team />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Landing />} />
      </Routes>
      <Toaster position="top-right" richColors />
    </>
  );
}
