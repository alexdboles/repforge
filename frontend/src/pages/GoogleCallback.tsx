import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { apiPost } from '@/lib/api';
import { clearGoogleProof, googleError, readGoogleProof } from '@/lib/google-auth';
import type { GoogleExchangeResponse, GoogleExchangeRequest, GoogleRecoveryResponse } from '@/lib/google-auth';
import { setToken, setUserId } from '@/lib/profile';
import { beginSession } from '@/lib/session';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import GoogleSignInButton from '@/components/GoogleSignInButton';

export default function GoogleCallback({ state, sessionId }: { state: string | null; sessionId: string | null }) {
  const navigate = useNavigate();
  const processed = useRef(false);
  const [proof] = useState(() => readGoogleProof(state));
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [hasPassword, setHasPassword] = useState(true);
  const [needsHelp, setNeedsHelp] = useState(false);
  const accept = (result: GoogleExchangeResponse) => {
    if (result.status === 'link_required') {
      setEmail(result.email || 'your Google email');
      setHasPassword(result.password_available !== false);
      setNeedsHelp(result.password_available === false);
      return;
    }
    if (!result.session) { setError('Sign-in did not return a valid RepForge session. Please start again.'); return; }
    setToken(result.session.token);
    setUserId(result.session.user.id);
    clearGoogleProof();
    beginSession();
    navigate('/dashboard', { replace: true });
  };
  const exchange = useMutation({ mutationFn: (payload: GoogleExchangeRequest) =>
    apiPost<GoogleExchangeResponse>('/auth/google/exchange', payload, { timeoutMs: 30000 }),
    onSuccess: accept, onError: e => setError(googleError(e)), retry: false });
  const connect = useMutation({ mutationFn: () => apiPost<GoogleExchangeResponse>('/auth/google/link', { ...proof, password }, { timeoutMs: 30000 }),
    onSuccess: accept, onError: e => { setPassword(''); setError(googleError(e)); }, retry: false });
  const recovery = useMutation({ mutationFn: () => apiPost<GoogleRecoveryResponse>('/auth/google/recovery', { ...proof }, { timeoutMs: 30000 }),
    onSuccess: () => setError(''), onError: e => setError(googleError(e)), retry: false });
  const { mutate } = exchange;
  useEffect(() => {
    if (processed.current) return;
    processed.current = true;
    // Discard the temporary credential before any unrelated page/API can observe it.
    // React Router is updated by navigate on completion; callback stays mounted meanwhile.
    window.history.replaceState(null, '', '/dashboard');
    if (!proof || !sessionId) { setError('This Google sign-in was cancelled, expired or started in a different tab. Please start again.'); return; }
    mutate({ ...proof, session_id: sessionId });
  }, [mutate, proof, sessionId]);
  return <main className='min-h-screen bg-background px-5 py-14' data-testid='google-callback-page'>
    <section className='mx-auto max-w-md rounded-xl border bg-card p-7 shadow-sm' aria-busy={exchange.isPending || connect.isPending}>
      <Link to='/' className='font-heading text-xl font-extrabold tracking-tight' data-testid='google-callback-brand'>RepForge</Link>
      <h1 className='mt-6 font-heading text-xl font-bold' data-testid='google-callback-heading'>{email ? needsHelp ? 'Connect without guessing a password' : 'Keep your existing practice history' : error ? 'Let’s try signing in again' : 'Google sign-in'}</h1>
      {!email && !error ? <p role='status' className='mt-3 text-sm text-muted-foreground' data-testid='google-callback-status'>Securely checking your Google identity…</p> : null}
      {email ? <p className='mt-4 text-sm leading-relaxed text-muted-foreground' data-testid='google-link-explanation'>Google sign-in succeeded. We found an existing RepForge record for <strong>{email}</strong>. {needsHelp ? 'We’ll protect its saved practice while your account connection is checked.' : 'If you have a RepForge password, use it to connect this account. Otherwise, choose the help option below.'} This is not your Google password.</p> : null}
      {email && !needsHelp && hasPassword ? <form className='mt-4 space-y-4' data-testid='google-link-form' onSubmit={e => { e.preventDefault(); setError(''); connect.mutate(); }}>
        <Label htmlFor='google-link-password' data-testid='google-link-password-label'>Existing RepForge password</Label>
        <Input id='google-link-password' data-testid='google-link-password' type='password' autoComplete='current-password' required maxLength={200} value={password} onChange={e => setPassword(e.target.value)} />
        <Button type='submit' className='w-full' data-testid='google-link-submit' disabled={!password || connect.isPending}>{connect.isPending ? 'Connecting your account…' : 'Connect Google & continue'}</Button>
      </form> : null}
      {email && !needsHelp ? <Button type='button' variant='outline' className='mt-3 w-full' data-testid='google-no-password-help' onClick={() => { setNeedsHelp(true); setPassword(''); setError(''); }}>I never set or don’t know that password</Button> : null}
      {email && needsHelp ? <section className='mt-4 rounded-lg border bg-muted/30 p-4' data-testid='google-recovery-panel'>
        <p className='text-sm leading-relaxed' data-testid='google-recovery-explanation'>{hasPassword ? 'You do not need to create or guess a password.' : 'No RepForge password is set on this account.'} Request a secure account connection, then share its reference with the person administering this RepForge app. Only an approved connection can unlock the existing history.</p>
        {recovery.data ? <div className='mt-4 space-y-2' data-testid='google-recovery-confirmation'>
          <p className='text-sm font-semibold' data-testid='google-recovery-status'>Account-connection request saved</p>
          <p className='text-xs text-muted-foreground' data-testid='google-recovery-notification'>No email has been sent. Share this non-secret reference with the app administrator; do not share passwords or sign-in links.</p>
          <code className='block select-all break-all rounded border bg-background p-2 text-sm' data-testid='google-recovery-reference'>{recovery.data.reference}</code>
          <p className='text-xs text-muted-foreground' data-testid='google-recovery-next-step'>After approval, choose Continue with Google below. Your original account, permissions and practice will be kept.</p>
        </div> : <Button className='mt-4 w-full' data-testid='google-request-recovery' disabled={recovery.isPending} onClick={() => recovery.mutate()}>{recovery.isPending ? 'Saving your request…' : 'Request a secure account connection'}</Button>}
        {hasPassword ? <Button variant='link' className='mt-3 px-0' data-testid='google-return-password' onClick={() => { setNeedsHelp(false); setError(''); }}>Use my RepForge password instead</Button> : null}
      </section> : null}
      {error ? <p role='alert' className='mt-4 text-sm text-red-700' data-testid='google-callback-error'>{error}</p> : null}
      {error || email ? <div className='mt-5'><GoogleSignInButton disabled={exchange.isPending || connect.isPending} /></div> : null}
      <Link to='/?signin=google' className='mt-5 inline-block text-sm font-semibold text-primary' data-testid='google-callback-cancel' onClick={clearGoogleProof}>Back to password sign-in or guest demo</Link>
    </section>
  </main>;
}