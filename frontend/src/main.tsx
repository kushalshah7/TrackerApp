import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {api} from './api';
import {authConfigured, initializeAuth, msal, signIn, signOut} from './auth';
import './styles.css';

type Viewer = Awaited<ReturnType<typeof api.me>>;

function AuthGate() {
  const [viewer, setViewer] = useState<Viewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    initializeAuth().then(async () => {
      if (msal.getAllAccounts().length && active) {
        const result = await api.me();
        if (active) setViewer(result);
      }
    }).catch((cause: Error) => {if (active) setError(cause.message);})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, []);

  const login = async () => {
    setLoading(true); setError('');
    try { await signIn(); setViewer(await api.me()); }
    catch (cause) {setError(cause instanceof Error ? cause.message : 'Sign-in failed');}
    finally {setLoading(false);}
  };
  const logout = async () => {
    try { await signOut(); setViewer(null); }
    catch (cause) {setError(cause instanceof Error ? cause.message : 'Sign-out failed');}
  };

  if (viewer) return <App viewer={viewer} onSignOut={logout}/>;
  return <main className="sign-in-page"><section className="form-card sign-in-card">
    <h1>Presales Tracker</h1>
    <p>Sign in with your Microsoft work account to access your team records.</p>
    {error && <p role="alert">{error}</p>}
    <button className="primary" onClick={login} disabled={loading || !authConfigured}>
      {loading ? 'Checking sign-in…' : 'Sign in with Microsoft'}
    </button>
  </section></main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><AuthGate/></React.StrictMode>);
