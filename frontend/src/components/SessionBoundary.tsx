import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Navigate, useLocation } from 'react-router-dom';
import { apiGet, ApiError } from '@/lib/api';
import { getUserId, setUserId } from '@/lib/profile';
import type { UserProfile } from '@/lib/types';
import { Button } from '@/components/ui/button';

export default function SessionBoundary({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const { pathname } = useLocation();
  const publicPage = pathname === '/' || pathname === '/sample-report';
  const session = useQuery({ queryKey: ['session'], queryFn: () => apiGet<UserProfile>('/auth/me'),
    enabled: !publicPage, retry: false, staleTime: 30000 });
  useEffect(() => {
    if (session.data) {
      if (getUserId() && getUserId() !== session.data.id) {
        qc.removeQueries({ predicate: q => q.queryKey[0] !== 'session' });
      }
      setUserId(session.data.id);
    }
  }, [session.data, qc]);
  useEffect(() => {
    const reset = () => { qc.clear(); void qc.invalidateQueries({ queryKey: ['session'] }); };
    const expired = () => { qc.clear(); window.location.assign('/'); };
    const storage = (e: StorageEvent) => { if (e.key === 'repforge.session-change') window.location.reload(); };
    window.addEventListener('repforge-session-changed', reset);
    window.addEventListener('repforge-session-expired', expired);
    window.addEventListener('storage', storage);
    return () => {
      window.removeEventListener('repforge-session-changed', reset);
      window.removeEventListener('repforge-session-expired', expired);
      window.removeEventListener('storage', storage);
    };
  }, [qc]);
  if (publicPage) return children;
  if (session.error instanceof ApiError && session.error.status === 401) return <Navigate to='/' replace />;
  if (session.isError) return <section className='p-8' data-testid='session-recovery'><h1>RepForge</h1><p>We could not verify your session. Your records are safe.</p><Button data-testid='session-retry' onClick={() => void session.refetch()}>Retry sign-in check</Button></section>;
  if (!session.data) return <div className='p-8' data-testid='session-checking'>RepForge · Checking your session…</div>;
  setUserId(session.data.id);
  return children;
}