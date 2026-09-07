import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiGet, apiPost, ApiError } from '@/lib/api';
import { beginSession } from '@/lib/session';
import { clearToken, clearUserId } from '@/lib/profile';
import { Button } from '@/components/ui/button';

export default function AccountRecovery() {
  const { pathname } = useLocation();
  const resetting = pathname === '/reset-password';
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get('token') ?? '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const info = useQuery({ queryKey: ['site-info'], queryFn: () => apiGet<{ password_recovery: boolean }>('/site-info') });
  useEffect(() => {
    if (resetting) window.history.replaceState(null, '', '/reset-password');
  }, [resetting]);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (resetting && (password !== confirm || new TextEncoder().encode(password).length > 72)) {
      setMessage('Passwords must match and use at most 72 UTF-8 bytes.'); return;
    }
    setBusy(true); setMessage('');
    try {
      const result = await apiPost<{ message: string }>(resetting ? '/auth/reset-password' : '/auth/forgot-password',
        resetting ? { token, password } : { email });
      if (resetting) { clearToken(); clearUserId(); beginSession(); setPassword(''); setConfirm(''); }
      setDone(true); setMessage(result.message);
    } catch (error) {
      const detail = error instanceof ApiError ? (error.body as { detail?: unknown })?.detail : null;
      setMessage(typeof detail === 'string' ? detail : 'Could not complete your request. Please try again.');
    } finally { setBusy(false); }
  }
  return <main className='mx-auto max-w-md px-6 py-16'>
    <Link to='/' className='font-bold'>RepForge</Link>
    <h1 className='mt-8 text-2xl font-bold'>{resetting ? 'Choose a new password' : 'Recover your account'}</h1>
    <p className='my-4 text-sm text-muted-foreground'>{resetting ? 'Updating your password signs out previous sessions.' : 'Enter your account email to request a reset link.'}</p>
    {resetting && !token ? <p>This link is missing its reset code. <Link to='/forgot-password'>Request a new link.</Link></p> :
      !resetting && !info.data?.password_recovery ? <p role='status'>{info.isPending ? 'Checking availability…' : 'Email recovery is not available right now.'} <Link to='/support'>Contact support.</Link></p> :
      !done && <form onSubmit={submit} className='space-y-4'>
        {resetting ? <>
          <label className='block'>New password<input className='mt-2 w-full rounded border p-3' type='password' autoComplete='new-password' minLength={8} maxLength={72} required value={password} onChange={e => setPassword(e.target.value)} /></label>
          <label className='block'>Confirm password<input className='mt-2 w-full rounded border p-3' type='password' autoComplete='new-password' minLength={8} maxLength={72} required value={confirm} onChange={e => setConfirm(e.target.value)} /></label>
        </> : <label className='block'>Email<input className='mt-2 w-full rounded border p-3' type='email' autoComplete='email' required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} /></label>}
        <Button disabled={busy} type='submit'>{busy ? 'Please wait…' : resetting ? 'Update password' : 'Send reset link'}</Button>
      </form>}
    <p role='status' className='my-5 text-sm'>{message}</p>
    <Link to='/?signin=google' className='text-primary'>Back to sign in</Link>
  </main>;
}
