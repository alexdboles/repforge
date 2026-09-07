import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ApiError, apiDelete } from '@/lib/api';
import type { DeletionResult } from '@/lib/privacy';
import { clearDeletedSession } from '@/lib/session';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

export default function DeleteDataDialog({ scope, sessionId, onClose }: { scope: 'account' | 'guest' | 'session'; sessionId?: string; onClose: () => void }) {
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const qc = useQueryClient();
  const title = scope === 'session' ? 'Permanently delete this session?' : scope === 'guest' ? 'Clear this guest’s data?' : 'Permanently delete your account?';
  const deletion = useMutation({
    mutationFn: () => apiDelete<DeletionResult>(`/data/${scope === 'session' ? `sessions/${sessionId}` : scope}?confirm=${encodeURIComponent(confirmation)}`),
    onSuccess: async (result) => {
      if (scope !== 'session') { clearDeletedSession(); return; }
      await qc.cancelQueries();
      qc.removeQueries({ predicate: q => ['simulation', 'scorecard', 'hint'].includes(String(q.queryKey[0])) });
      await qc.invalidateQueries();
      toast.success(result.message);
      onClose();
    },
    onError: (err) => {
      const detail = err instanceof ApiError ? (err.body as { detail?: unknown })?.detail : null;
      setError(typeof detail === 'string' ? detail : 'Deletion could not be confirmed. Nothing is reported as deleted. Please retry.');
    },
  });
  return <Dialog open onOpenChange={open => { if (!open && !deletion.isPending) onClose(); }}>
    <DialogContent data-testid='delete-data-dialog' showCloseButton={!deletion.isPending}>
      <DialogHeader><DialogTitle data-testid='delete-data-title'>{title}</DialogTitle><DialogDescription data-testid='delete-data-description'>
        {scope === 'session' ? 'This also deletes linked retries and moment drills, feedback and AI voice cache. Derived earlier-call memory and streak reset; XP from deleted calls is removed. Other sessions stay.' : 'This permanently removes your profile, simulations, transcripts, evaluations, sales profiles, memberships and linked sign-in records from RepForge’s active database. All your sessions will stop working. Other people’s records stay.'}
      </DialogDescription></DialogHeader>
      <p data-testid='delete-data-limits' className='text-sm text-muted-foreground'>There is no undo. Download your JSON first if you want a copy. Provider-held data, private backups, infrastructure logs and files you downloaded are not erased by this action.</p>
      <div><Label htmlFor='delete-confirmation' data-testid='delete-data-label'>Type DELETE to confirm</Label><Input id='delete-confirmation' data-testid='delete-data-confirmation' autoComplete='off' value={confirmation} onChange={e => setConfirmation(e.target.value)} disabled={deletion.isPending} className='mt-2' /></div>
      {error && <p role='alert' data-testid='delete-data-error' className='text-sm text-red-700'>{error}</p>}
      <div className='flex justify-end gap-3'><Button variant='outline' data-testid='delete-data-cancel' disabled={deletion.isPending} onClick={onClose}>Keep my data</Button><Button variant='destructive' data-testid='delete-data-submit' disabled={confirmation !== 'DELETE' || deletion.isPending} onClick={() => { setError(''); deletion.mutate(); }}>{deletion.isPending ? 'Deleting…' : 'Permanently delete'}</Button></div>
    </DialogContent>
  </Dialog>;
}