import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, ApiError } from '@/lib/api';
import type { InvitationResponse, UserProfile } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function WorkspaceAccess({ user }: { user: UserProfile }) {
  const qc = useQueryClient();
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('');
  const fail = (e: unknown) => setMessage(e instanceof ApiError ? String((e.body as {detail?: string}).detail ?? 'Request failed') : 'Connection failed');
  const invite = useMutation({ mutationFn: () => apiPost<InvitationResponse>('/workspace/invitations', { email, role: 'member' }), onError: fail });
  const join = useMutation({ mutationFn: () => apiPost<UserProfile>('/workspace/join', { token }), onSuccess: () => { qc.clear(); window.location.reload(); }, onError: fail });
  const personal = useMutation({ mutationFn: () => apiPost<UserProfile>('/workspace/personal'), onSuccess: () => { qc.clear(); window.location.reload(); }, onError: fail });
  return <section className='my-6 rounded-xl border bg-card p-5' data-testid='workspace-access'>
    <h2 className='font-heading font-bold' data-testid='workspace-heading'>Verified workspace access</h2>
    <p className='mt-2 text-sm text-muted-foreground' data-testid='workspace-privacy'>Your personal records stay yours. A matching company name never creates team membership. Invite only colleagues you authorise to join.</p>
    {!user.is_guest && ['owner', 'admin', 'manager'].includes(user.workspace_role) ? <div className='mt-4'>
      <Label htmlFor='invite-email' data-testid='invite-email-label'>Colleague’s account email</Label>
      <Input id='invite-email' data-testid='invite-email' value={email} onChange={e => setEmail(e.target.value)} type='email' />
      <Button className='mt-2' data-testid='create-invite' disabled={invite.isPending || !email.includes('@')} onClick={() => invite.mutate()}>Create private invitation</Button>
      {invite.data ? <div className='mt-3 text-sm' data-testid='invite-result'><p>Share this one-time invitation privately with that colleague. Expires in 48 hours. No email is sent.</p><code className='block break-all select-all' data-testid='invite-token'>{invite.data.token}</code></div> : null}
    </div> : null}
    {!user.is_guest ? <div className='mt-4'>
      <Label htmlFor='join-token' data-testid='join-token-label'>Invitation code addressed to your account email</Label>
      <Input id='join-token' data-testid='join-token' value={token} onChange={e => setToken(e.target.value)} />
      <div className='mt-2 flex flex-wrap gap-2'><Button data-testid='join-workspace' disabled={join.isPending || token.length < 20} onClick={() => join.mutate()}>Join invited workspace</Button><Button variant='outline' data-testid='personal-workspace' disabled={personal.isPending} onClick={() => personal.mutate()}>Use personal workspace</Button></div>
    </div> : <p className='mt-3 text-sm' data-testid='guest-workspace-note'>Guest practice is isolated. Create an account to use teams.</p>}
    {message ? <p role='alert' className='mt-3 text-sm text-red-700' data-testid='workspace-error'>{message}</p> : null}
  </section>;
}