import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import type { EvidenceSummary } from '@/lib/types';
import AppShell from '@/components/AppShell';
import { useCurrentUser } from '@/lib/use-current-user';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function EvidencePage() {
  const { data: user } = useCurrentUser();
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const query = new URLSearchParams({ ...(start ? { start } : {}), ...(end ? { end } : {}) });
  const data = useQuery({ queryKey: ['owner-evidence', start, end], queryFn: () => apiGet<EvidenceSummary>(`/owner/evidence?${query}`), enabled: Boolean(user?.is_admin), retry: false });
  return <AppShell><section data-testid='owner-evidence-page'>
    <h1 className='font-heading text-3xl font-bold' data-testid='evidence-title'>RepForge evidence</h1>
    <p className='mt-2 text-sm text-muted-foreground' data-testid='evidence-intro'>Private owner summary · observed usage, not marketing estimates</p>
    {!user?.is_admin ? <p className='mt-5' data-testid='evidence-access-restricted'>Platform owner access is required. Workspace ownership does not grant access to other workspaces’ usage.</p> : <>
      <div className='mt-6 flex flex-wrap items-end gap-4'><div><Label htmlFor='evidence-from' data-testid='evidence-from-label'>From (UTC)</Label><Input id='evidence-from' type='date' data-testid='evidence-from' value={start} onChange={e => setStart(e.target.value)} /></div><div><Label htmlFor='evidence-until' data-testid='evidence-until-label'>Through (UTC)</Label><Input id='evidence-until' type='date' data-testid='evidence-until' value={end} onChange={e => setEnd(e.target.value)} /></div><Button variant='outline' data-testid='evidence-refresh' onClick={() => void data.refetch()}>Refresh evidence</Button></div>
      {data.isError ? <p className='mt-5 text-red-700' role='alert' data-testid='evidence-error'>Could not load evidence. Check dates and owner permissions, then refresh.</p> : null}
      {data.isPending ? <p className='mt-5' data-testid='evidence-loading'>Loading instrumented usage…</p> : null}
      {data.data ? <><p className='mt-5 text-sm' data-testid='evidence-date-range'>{data.data.start} – {data.data.end} · {data.data.sample_size} unique practice users</p><dl className='mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3'>{([
        ['Demo starts', data.data.demo_starts], ['Successful first replies', data.data.first_replies], ['Completed grading', data.data.completed_grading],
        ['Demo cohort completion', `${data.data.completion_rate}%`], ['Return users', data.data.returning_users], ['Retry starts', data.data.retry_starts],
        ['Retry completions', data.data.retry_completions], ['Higher comparable target scores', data.data.comparable_improvements], ['Optional feedback', `${data.data.feedback_count} ratings · ${data.data.feedback_average ?? 'unassessed'}/5`],
      ] as [string, number | string][]).map(([label, value], i) => <div className='rounded-lg border bg-card p-5' key={label} data-testid={`evidence-metric-${i}`}><dt className='text-sm text-muted-foreground'>{label}</dt><dd className='mt-2 font-heading text-2xl font-bold'>{value}</dd></div>)}</dl><p className='mt-5 rounded-lg border p-4 text-sm leading-relaxed text-muted-foreground' data-testid='evidence-methodology'>{data.data.note}</p></> : null}
    </>}
  </section></AppShell>;
}