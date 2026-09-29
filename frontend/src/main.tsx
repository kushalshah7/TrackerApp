import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {ApiError, api} from './api';
import {authClient, authConfigured} from './auth';
import './styles.css';

type Viewer = Awaited<ReturnType<typeof api.me>>;
type Mode = 'sign-in' | 'sign-up' | 'invite' | 'forgot' | 'reset';

function AuthGate() {
  const [viewer, setViewer] = useState<Viewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<Mode>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    if (!authClient) {setError('Tracker sign-in is not configured.'); setLoading(false); return;}
    authClient.getSession().then(async ({data, error: sessionError}) => {
      if (sessionError) throw sessionError;
      if (!data?.session || !data.user || !active) return;
      setEmail(data.user.email);
      try {const result = await api.me(); if (active) setViewer(result);}
      catch (cause) {
        if (active && cause instanceof ApiError && cause.status === 403) setMode('invite');
        else throw cause;
      }
    }).catch((cause: Error) => {if (active) setError(cause.message);})
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
          otp: inviteCode.trim(), password});
        if (result.error) throw result.error;
        setMode('sign-in'); setPassword(''); setInviteCode('');
        setMessage('Password updated. Sign in with your new password.');
        return;
      }
      if (mode === 'sign-up') {
        const result = await authClient.signUp.email({email: email.trim().toLowerCase(), password,
          name: email.split('@')[0] || 'Tracker user'});
        if (result.error) throw result.error;
      }
      const session = await authClient.getSession();
      if (mode === 'invite' && !session.data?.session) {
        setMode('sign-in');
        throw new Error('Your session expired. Sign in again before activating access.');
      }
      if (mode === 'sign-in' || !session.data?.session) {
        const result = await authClient.signIn.email({email: email.trim().toLowerCase(), password,
          rememberMe: true});
        if (result.error) throw result.error;
      }
      if (mode === 'sign-up' || mode === 'invite') await api.enroll(inviteCode.trim());
      try {setViewer(await api.me()); setPassword(''); setInviteCode('');}
      catch (cause) {
        if (cause instanceof ApiError && cause.status === 403) setMode('invite');
        else throw cause;
      }
    } catch (cause) {setError(cause instanceof Error ? cause.message : 'Sign-in failed');}
    finally {setLoading(false);}
  };
  const logout = async () => {
    try {await authClient?.signOut(); setViewer(null); setPassword(''); setMode('sign-in');}
    catch (cause) {setError(cause instanceof Error ? cause.message : 'Sign-out failed');}
  };

  if (viewer) return <App viewer={viewer} onSignOut={logout}/>;
  return <main className="sign-in-page"><section className="form-card sign-in-card">
    <h1>Presales Tracker</h1>
    <p>{mode === 'invite' ? `Enter the one-time invitation code for ${email}.` :
      mode === 'forgot' || mode === 'reset' ? 'Reset your tracker password using a code sent to your work email.' :
      'Use your approved work email and a separate password for this tracker.'}</p>
    {error && <p role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    <form onSubmit={submit} className="sign-in-form">
      {mode !== 'invite' && <label>Work email<input type="email" value={email} onChange={event => setEmail(event.target.value)} required autoComplete="email"/></label>}
      {mode !== 'forgot' && mode !== 'invite' && <label>{mode === 'reset' ? 'New tracker password' : 'Tracker password'}<input type="password" value={password} onChange={event => setPassword(event.target.value)} required minLength={mode === 'sign-up' || mode === 'reset' ? 12 : undefined} autoComplete={mode === 'sign-up' || mode === 'reset' ? 'new-password' : 'current-password'}/></label>}
      {(mode === 'sign-up' || mode === 'invite' || mode === 'reset') && <label>{mode === 'reset' ? 'Email reset code' : 'One-time invitation code'}<input value={inviteCode} onChange={event => setInviteCode(event.target.value)} required autoComplete="off"/></label>}
      {mode === 'sign-up' && <small>Create a new password for this tracker. Do not reuse your Microsoft work password.</small>}
      <button className="primary" disabled={loading || !authConfigured}>{loading ? 'Please wait…' : mode === 'sign-up' ? 'Create account' : mode === 'invite' ? 'Activate access' : mode === 'forgot' ? 'Send reset code' : mode === 'reset' ? 'Set new password' : 'Sign in'}</button>
    </form>
    {mode !== 'invite' && <button type="button" className="auth-switch" onClick={() => {setMode(mode === 'sign-in' ? 'sign-up' : 'sign-in'); setError(''); setMessage('');}}>
      {mode === 'sign-in' ? 'New team member? Sign up' : 'Back to sign in'}
    </button>}
    {mode === 'sign-in' && <button type="button" className="auth-switch" onClick={() => {setMode('forgot'); setError('');}}>Forgot password?</button>}
    {mode === 'invite' && <button type="button" className="auth-switch" onClick={logout}>Use another account</button>}
  </section></main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><AuthGate/></React.StrictMode>);
