import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Download, Trash2, Database, FileText, ArrowUpRight } from 'lucide-react';
import { apiGet, ApiError } from '@/lib/api';
import { getUserId } from '@/lib/profile';
import type { DataExport, DataSummary } from '@/lib/privacy';
import DataLayout from '@/components/DataLayout';
import DeleteDataDialog from '@/components/DeleteDataDialog';
import { Button, buttonVariants } from '@/components/ui/button';

export default function Data() {
  const userId = getUserId();
  const [showDelete, setShowDelete] = useState(false);
  const [exportStatus, setExportStatus] = useState('');
  const summary = useQuery({ queryKey: ['data-summary', userId], queryFn: () => apiGet<DataSummary>('/data/summary'), enabled: Boolean(userId), retry: false });
  const download = useMutation({ mutationFn: () => apiGet<DataExport>('/data/export'),
    onSuccess: data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `repforge-data-${data.exported_at.slice(0, 10)}.json`; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setExportStatus('Your JSON download is ready. Keep this file private; deleting your account will not erase downloaded copies.');
    }, onError: () => setExportStatus('Export failed. No file was created. Please try again.'),
  });
  const signedOut = !userId || summary.error instanceof ApiError && summary.error.status === 401;
  return <DataLayout title='You’re in control of your data.' eyebrow='Data & controls'>
    <p data-testid='data-intro' className='-mt-5 mb-8 max-w-2xl text-base leading-relaxed text-muted-foreground'>See what your practice leaves behind. Take a copy, remove a session, or leave without leaving your training records in the active database.</p>
    {signedOut ? <section data-testid='data-signin-notice' className='rounded-xl border border-border bg-card p-6'><h2 data-testid='data-signin-title' className='font-heading text-lg font-bold'>Controls are private to your session</h2><p data-testid='data-signin-copy' className='mb-5 mt-2 text-sm leading-6 text-muted-foreground'>Sign in to export or delete your account data. For guest practice, open this page from the same guest session before signing out. A lost guest session cannot be recovered by its ID alone.</p><Link to='/?signin=google' data-testid='data-signin-link' className={buttonVariants()}>Sign in or continue as guest</Link></section> : <>
      {summary.isError && <div role='alert' data-testid='data-load-error' className='mb-6 flex flex-wrap items-center gap-4 text-sm'>Your stored-data summary could not load.<Button variant='outline' data-testid='data-summary-retry' onClick={() => void summary.refetch()}>Retry</Button></div>}
      <div className='grid items-start gap-8 lg:grid-cols-[1fr_290px]'><div className='space-y-6'>
        <section className='rounded-xl border border-border bg-card p-6' data-testid='data-export-card'><Download className='mb-4 size-5 text-primary' /><h2 data-testid='data-export-title' className='font-heading text-xl font-bold'>Take your practice with you</h2><p data-testid='data-export-copy' className='mb-5 mt-3 text-sm leading-7 text-muted-foreground'>Download your profile, full transcripts, evaluations, coaching, saved business profiles, scenarios and personal activity as real JSON. No passwords, sign-in tokens or other members’ records.</p><Button data-testid='data-export-button' disabled={download.isPending || !summary.data || summary.isError} onClick={() => { setExportStatus(''); download.mutate(); }}><Download className='size-4' />{download.isPending ? 'Preparing JSON…' : 'Download my JSON'}</Button>{exportStatus && <p role='status' data-testid='data-export-status' className='mt-4 text-sm leading-6 text-muted-foreground'>{exportStatus}</p>}</section>
        <section className='rounded-xl border border-border bg-card p-6' data-testid='data-sessions-card'><FileText className='mb-4 size-5 text-primary' /><h2 data-testid='data-sessions-title' className='font-heading text-xl font-bold'>Remove a specific session</h2><p data-testid='data-sessions-copy' className='mt-3 text-sm leading-7 text-muted-foreground'>Delete a call from History. Its linked retries and moment drills are also removed because they contain copied conversation data. Other sessions remain. Progress recalculates from remaining records; streak resets.</p><Link to='/history' data-testid='data-history-link' className='mt-4 inline-flex items-center gap-2 text-sm font-semibold text-primary'>Manage session history<ArrowUpRight className='size-4' /></Link></section>
        <section className='rounded-xl border border-red-200 bg-red-50/40 p-6' data-testid='data-delete-card'><Trash2 className='mb-4 size-5 text-red-700' /><h2 data-testid='data-delete-title' className='font-heading text-xl font-bold'>{summary.data?.is_guest ? 'Clear this guest’s data' : 'Delete your RepForge account'}</h2><p data-testid='data-delete-copy' className='mb-5 mt-3 text-sm leading-7 text-muted-foreground'>{summary.data?.is_guest ? 'Guest does not mean temporary-only storage. This removes the current guest account and its stored practice, then clears this browser’s RepForge session.' : 'Permanently erase your active-database account and training data, disconnect linked sign-in, and invalidate all your sessions. This does not delete your Google account.'}</p><Button variant='outline' className='border-red-200 text-red-700 hover:bg-red-100' data-testid='data-delete-button' disabled={!summary.data || summary.isError} onClick={() => setShowDelete(true)}>{summary.data?.is_guest ? 'Clear guest data' : 'Delete my account'}</Button></section>
      </div><aside className='rounded-xl border border-border bg-slate-900 p-6 text-slate-100' data-testid='data-inventory'><Database className='mb-4 size-5 text-sky-300' /><h2 data-testid='data-inventory-title' className='font-heading text-base font-bold'>Your stored practice</h2><dl className='my-6 space-y-4'>{[['simulations', 'Sessions, including retries'], ['sales_profiles', 'Business profiles'], ['custom_scenarios', 'Custom scenarios']].map(([key, label]) => <div key={key} className='flex items-center justify-between gap-3'><dt data-testid={`data-count-label-${key}`} className='text-xs text-slate-300'>{label}</dt><dd data-testid={`data-count-${key}`} className='font-mono text-lg'>{summary.isError ? '—' : summary.data?.counts[key] ?? '…'}</dd></div>)}</dl><p data-testid='data-retention' className='border-t border-slate-700 pt-5 text-xs leading-6 text-slate-300'>{summary.data?.retention ?? 'Records remain until you explicitly delete them.'}</p></aside></div>
    </>}
    <section className='mt-10 max-w-3xl border-t border-border pt-7' data-testid='data-limits'><h2 data-testid='data-limits-title' className='font-heading text-base font-bold'>What these controls cannot erase</h2><p data-testid='data-limits-copy' className='mt-3 text-sm leading-7 text-muted-foreground'>Provider-held copies, infrastructure logs, private operator backups and JSON already downloaded to a device are separate. Zero-retention provider settings and a fixed backup purge schedule have not been verified. No automatic guest-account cleanup is scheduled. <Link to='/privacy' data-testid='data-privacy-details' className='font-semibold text-primary'>Read the full privacy notice.</Link></p></section>
    {showDelete && summary.data && <DeleteDataDialog scope={summary.data.is_guest ? 'guest' : 'account'} onClose={() => setShowDelete(false)} />}
  </DataLayout>;
}