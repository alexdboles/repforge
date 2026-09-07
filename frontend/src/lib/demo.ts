import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { apiGet, apiPost, ApiError } from './api';
import { getUserId, setToken, setUserId } from './profile';
import { beginSession } from './session';
import type { SessionResponse, Simulation, UserProfile } from './types';

export function useDemoLaunch() {
  const navigate = useNavigate();
  return useMutation({ mutationFn: async () => {
    let user: UserProfile | undefined;
    if (getUserId()) {
      try { user = await apiGet<UserProfile>('/auth/me'); }
      catch (e) { if (!(e instanceof ApiError) || e.status !== 401) throw e; }
    }
    if (!user) {
      const session = await apiPost<SessionResponse>('/auth/guest');
      setToken(session.token); setUserId(session.user.id); beginSession(); user = session.user;
    }
    return apiPost<Simulation>('/simulations', { user_id: user.id, exercise_id: 'cold-call', difficulty: 2, scenario_id: 'crm-vp-sales', is_demo: true });
  }, onSuccess: sim => navigate(`/simulation/${sim.id}`), onError: e => {
    const message = e instanceof ApiError ? (e.body as { detail?: string }).detail : '';
    toast.error(typeof message === 'string' ? message : 'Could not start the demo. Please try again.');
  } });
}