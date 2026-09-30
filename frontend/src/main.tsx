import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {ApiError, api} from './api';
import {authClient, authConfigured} from './auth';
import './styles.css';

type Viewer = Awaited<ReturnType<typeof api.me>>;
type Mode = 'sign-in' | 'sign-up' | 'forgot' | 'reset';

function invitationFromLink() {
  const url = new URL(window.location.href);
  const fragment = new URLSearchParams(url.hash.slice(1));
  const token = (fragment.get('invite') || url.searchParams.get('invite'))?.trim();
  if (token) sessionStorage.setItem('tracker-invite', token);
  if (url.searchParams.has('invite') || fragment.has('invite')) {
    url.searchParams.delete('invite');
    fragment.delete('invite');
    url.hash = fragment.toString();
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
  }
  return sessionStorage.getItem('tracker-invite') || '';
}

function errorMessage(cause: unknown) {
  return cause && typeof cause === 'object' && 'message' in cause && typeof cause.message === 'string'
    ? cause.message : 'Unable to complete sign-in. Please try again.';
}

function AuthGate() {
  const [viewer, setViewer] = useState<Viewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [inviteToken, setInviteToken] = useState(invitationFromLink);
  const [mode, setMode] = useState<Mode>(inviteToken ? 'sign-up' : 'sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    if (!authClient) {setError('Tracker sign-in is not configured.'); setLoading(false); return;}
    authClient.getSession().then(async ({data, error: sessionError}) => {
      if (sessionError) throw sessionError;
      if (!data?.session || !data.user || !active) return;
      setEmail(data.user.email);
      try {const result = await api.me(); if (active) {setViewer(result); sessionStorage.removeItem('tracker-invite'); setInviteToken('');}}
      catch (cause) {
        if (cause instanceof ApiError && cause.status === 403 && inviteToken) {
          await api.enroll(inviteToken);
          const result = await api.me();
          if (active) {setViewer(result); sessionStorage.removeItem('tracker-invite'); setInviteToken('');}
        } else throw cause;
      }
    }).catch((cause: unknown) => {if (active) setError(errorMessage(cause));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!authClient) return;
    setLoading(true); setError(''); setMessage('');
    try {
      if (mode === 'forgot') {
        const result = await authClient.forgetPassword.emailOtp({email: email.trim().toLowerCase()});
        if (result.error) throw result.error;
        setMode('reset'); setMessage('Check your email for the reset code.');
        return;
      }
      if (mode === 'reset') {
        const result = await authClient.emailOtp.resetPassword({email: email.trim().toLowerCase(),
          otp: resetCode.trim(), password});
        if (result.error) throw result.error;
        setMode('sign-in'); setPassword(''); setResetCode('');
        setMessage('Password updated. Sign in with your new password.');
        return;
      }
      if (mode === 'sign-up') {
        if (!inviteToken) throw new Error('Open your private signup link to create an account.');
        await api.checkInvite(email.trim().toLowerCase(), inviteToken);
        const result = await authClient.signUp.email({email: email.trim().toLowerCase(), password,
          name: email.split('@')[0] || 'Tracker user'});
        if (result.error) throw result.error;
        setMode('sign-in');
      }
      const session = await authClient.getSession();
      if (mode === 'sign-in' || !session.data?.session) {
        const result = await authClient.signIn.email({email: email.trim().toLowerCase(), password,
          rememberMe: true});
        if (result.error) throw result.error;
      }
      try {setViewer(await api.me()); setPassword(''); sessionStorage.removeItem('tracker-invite'); setInviteToken('');}
      catch (cause) {
        if (cause instanceof ApiError && cause.status === 403 && inviteToken) {
          await api.enroll(inviteToken);
          setViewer(await api.me());
          sessionStorage.removeItem('tracker-invite');
          setInviteToken('');
          setPassword('');
        } else throw cause;
      }
    } catch (cause) {setError(errorMessage(cause));}
    finally {setLoading(false);}
  };
  const logout = async () => {
    try {await authClient?.signOut(); setViewer(null); setPassword(''); setMode('sign-in');}
    catch (cause) {setError(errorMessage(cause));}
  };

  if (viewer) return <App viewer={viewer} onSignOut={logout}/>;
  return <main className="sign-in-page"><section className="form-card sign-in-card">
    <h1>Presales Tracker</h1>
    <p>{mode === 'forgot' || mode === 'reset' ? 'Reset your tracker password using a code sent to your work email.' :
      mode === 'sign-up' ? 'Create your account using your private signup link and a new tracker password.' :
      'Sign in with your approved work email and tracker password.'}</p>
    {error && <p role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    <form onSubmit={submit} className="sign-in-form">
      <label>Work email<input type="email" value={email} onChange={event => setEmail(event.target.value)} required autoComplete="email"/></label>
      {mode !== 'forgot' && <label>{mode === 'reset' ? 'New tracker password' : 'Tracker password'}<input type="password" value={password} onChange={event => setPassword(event.target.value)} required minLength={mode === 'sign-up' || mode === 'reset' ? 12 : undefined} autoComplete={mode === 'sign-up' || mode === 'reset' ? 'new-password' : 'current-password'}/></label>}
      {mode === 'reset' && <label>Email reset code<input value={resetCode} onChange={event => setResetCode(event.target.value)} required autoComplete="off"/></label>}
      {mode === 'sign-up' && <small>Create a new password for this tracker. Do not reuse your Microsoft work password.</small>}
      <button className="primary" disabled={loading || !authConfigured}>{loading ? 'Please wait…' : mode === 'sign-up' ? 'Create account' : mode === 'forgot' ? 'Send reset code' : mode === 'reset' ? 'Set new password' : 'Sign in'}</button>
    </form>
    {mode === 'sign-up' && <button type="button" className="auth-switch" onClick={() => {setMode('sign-in'); setError('');}}>Already have an account? Sign in</button>}
    {mode === 'sign-in' && inviteToken && <button type="button" className="auth-switch" onClick={() => {setMode('sign-up'); setError('');}}>Create account</button>}
    {mode === 'sign-in' && !inviteToken && <p className="sign-in-help">Need an account? Ask Kushal for your private signup link.</p>}
    {mode === 'sign-in' && <button type="button" className="auth-switch" onClick={() => {setMode('forgot'); setError('');}}>Forgot password?</button>}
    {(mode === 'forgot' || mode === 'reset') && <button type="button" className="auth-switch" onClick={() => {setMode('sign-in'); setError('');}}>Back to sign in</button>}
  </section></main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><AuthGate/></React.StrictMode>);
