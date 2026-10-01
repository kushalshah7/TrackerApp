import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {api} from './api';
import {authClient, authConfigured, clearAuthToken} from './auth';
import './styles.css';

type Viewer = Awaited<ReturnType<typeof api.me>>;
type Mode = 'sign-in' | 'sign-up' | 'verify' | 'forgot' | 'reset';

function errorMessage(cause: unknown) {
  return cause && typeof cause === 'object' && 'message' in cause && typeof cause.message === 'string'
    ? cause.message : 'Unable to complete sign-in. Please try again.';
}

function AuthGate() {
  const [viewer, setViewer] = useState<Viewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<Mode>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    sessionStorage.removeItem('tracker-invite');
    if (!authClient) {setError('Tracker sign-in is not configured.'); setLoading(false); return;}
    authClient.getSession().then(async ({data, error: sessionError}) => {
      if (sessionError) throw sessionError;
      if (!data?.session || !data.user || !active) return;
      setEmail(data.user.email);
      if (!data.user.emailVerified) {
        setMode('verify');
        setMessage('Verify your work email once to activate your account.');
        return;
      }
      const result = await api.me();
      if (active) setViewer(result);
    }).catch((cause: unknown) => {if (active) setError(errorMessage(cause));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, []);

  const sendVerification = async () => {
    if (!authClient) return;
    const result = await authClient.emailOtp.sendVerificationOtp({email: email.trim().toLowerCase(), type: 'email-verification'});
    if (result.error) throw result.error;
    setMode('verify'); setResetCode('');
    setMessage('Check your work email for the verification code. This is only needed once.');
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!authClient) return;
    setLoading(true); setError(''); setMessage('');
    clearAuthToken();
    try {
      if (mode === 'verify') {
        const result = await authClient.emailOtp.verifyEmail({email: email.trim().toLowerCase(), otp: resetCode.trim()});
        if (result.error) throw result.error;
        const session = await authClient.getSession();
        if (!session.data?.session) {
          setMode('sign-in'); setMessage('Email verified. Sign in with your password.'); setResetCode('');
          return;
        }
        setViewer(await api.me()); setPassword(''); setResetCode('');
        return;
      }
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
        const approved = await api.checkEmail(email.trim().toLowerCase());
        const result = await authClient.signUp.email({email: email.trim().toLowerCase(), password,
          name: approved.name});
        if (result.error) {
          if (result.error.code?.startsWith('USER_ALREADY_EXISTS')) {
            setMode('sign-in');
            setMessage('Your account already exists. Sign in with your tracker password, or use Forgot password.');
            return;
          }
          throw result.error;
        }
        setMode('sign-in');
      }
      if (mode === 'sign-in' || mode === 'sign-up') {
        const result = await authClient.signIn.email({email: email.trim().toLowerCase(), password,
          rememberMe: true});
        if (result.error) throw result.error;
      }
      const signedIn = await authClient.getSession();
      if (!signedIn.data?.session || !signedIn.data.user) throw new Error('Sign-in session was not saved. Check that cookies are enabled.');
      if (!signedIn.data.user.emailVerified) {
        await sendVerification();
        return;
      }
      setViewer(await api.me()); setPassword('');
    } catch (cause) {setError(errorMessage(cause));}
    finally {setLoading(false);}
  };
  const logout = async () => {
    clearAuthToken();
    try {await authClient?.signOut(); setViewer(null); setPassword(''); setMode('sign-in');}
    catch (cause) {setError(errorMessage(cause));}
  };

  if (viewer) return <App viewer={viewer} onSignOut={logout}/>;
  return <div className="auth-page">
    <header className="auth-masthead">
      <div className="auth-company"><span>INVECTO</span><span className="auth-company-divider" aria-hidden="true"/><span className="auth-product">Presales Tracker</span></div>
      <span className="auth-internal">Internal team portal</span>
    </header>
    <main className="sign-in-page"><section className="form-card sign-in-card" aria-labelledby="auth-title">
    <header className="auth-header">
      <p className="auth-eyebrow">TEAM WORKSPACE</p>
      <h1 id="auth-title">{mode === 'sign-up' ? 'Create your account' : mode === 'verify' ? 'Verify your email' : mode === 'forgot' ? 'Reset your password' : mode === 'reset' ? 'Choose a new password' : 'Sign in'}</h1>
      <p>{mode === 'verify' ? 'Confirm ownership of your work email once to activate your account.' :
      mode === 'forgot' || mode === 'reset' ? 'Reset your tracker password using a code sent to your work email.' :
      mode === 'sign-up' ? 'Create your account with your work email and a new tracker password.' :
      'Use your work email and tracker password to continue.'}</p>
    </header>
    {error && <div className="auth-feedback auth-feedback-error" role="alert">{error}</div>}
    {message && <div className="auth-feedback" role="status">{message}</div>}
    <form onSubmit={submit} className="sign-in-form">
      <label>Work email<input type="email" value={email} onChange={event => setEmail(event.target.value)} required readOnly={mode === 'verify'} autoComplete="email"/></label>
      {mode !== 'forgot' && mode !== 'verify' && <label>{mode === 'reset' ? 'New tracker password' : 'Tracker password'}<input type="password" value={password} onChange={event => setPassword(event.target.value)} required minLength={mode === 'sign-up' || mode === 'reset' ? 8 : undefined} aria-describedby={mode === 'sign-up' || mode === 'reset' ? 'auth-password-help' : undefined} autoComplete={mode === 'sign-up' || mode === 'reset' ? 'new-password' : 'current-password'}/></label>}
      {(mode === 'reset' || mode === 'verify') && <label>{mode === 'verify' ? 'Email verification code' : 'Email reset code'}<input value={resetCode} onChange={event => setResetCode(event.target.value)} required inputMode="numeric" autoComplete="one-time-code"/></label>}
      {(mode === 'sign-up' || mode === 'reset') && <small id="auth-password-help">Use at least 8 characters. Choose a tracker-only password, separate from your Microsoft work password.</small>}
      <button className="primary" disabled={loading || !authConfigured}>{loading ? 'Please wait…' : mode === 'sign-up' ? 'Create account' : mode === 'verify' ? 'Verify email' : mode === 'forgot' ? 'Send reset code' : mode === 'reset' ? 'Set new password' : 'Sign in'}</button>
    </form>
    <nav className={`auth-actions ${mode === 'sign-up' || mode === 'forgot' || mode === 'reset' ? 'auth-actions-single' : ''}`} aria-label="Account options">
    {mode === 'sign-up' && <button type="button" className="auth-switch" onClick={() => {setMode('sign-in'); setError(''); setMessage('');}}>Already registered? Sign in</button>}
    {mode === 'sign-in' && <button type="button" className="auth-switch" onClick={() => {setMode('sign-up'); setError(''); setMessage('');}}>Create account</button>}
    {mode === 'sign-in' && <button type="button" className="auth-switch" onClick={() => {setMode('forgot'); setError('');}}>Forgot password?</button>}
    {(mode === 'forgot' || mode === 'reset') && <button type="button" className="auth-switch" onClick={() => {setMode('sign-in'); setError('');}}>Back to sign in</button>}
    {mode === 'verify' && <><button type="button" className="auth-switch" disabled={loading} onClick={async () => {setLoading(true); setError(''); try {await sendVerification();} catch (cause) {setError(errorMessage(cause));} finally {setLoading(false);}}}>Resend email verification</button><button type="button" className="auth-switch" onClick={logout}>Use another account</button></>}
    </nav>
    <p className="auth-access-note">Access is restricted to approved Invecto employees.</p>
  </section></main>
    <footer className="auth-page-footer">Invecto · Presales operations</footer>
  </div>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><AuthGate/></React.StrictMode>);
