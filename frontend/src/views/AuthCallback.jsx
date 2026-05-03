import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * AuthCallback view.
 *
 * Handles the post-OAuth redirect. If the provider returns a token in the
 * query string, persist it to localStorage so ``useApi`` and AuthContext
 * pick it up. Then call ``auth.refresh()`` to load the current user. On
 * success, navigate to ``/``; on failure, send the user back to ``/login``.
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [params] = useSearchParams();
  const [status, setStatus] = useState('Finishing sign-in...');

  useEffect(() => {
    let cancelled = false;
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      setStatus('Sign-in failed.');
      const t = setTimeout(() => navigate('/login', { replace: true }), 800);
      return () => clearTimeout(t);
    }

    if (token) {
      try { localStorage.setItem('pst-auth-token', token); } catch { /* ignore */ }
    }

    (async () => {
      try {
        if (auth?.refresh) await auth.refresh();
      } catch { /* ignore */ }
      if (cancelled) return;
      // Determine where to send the user. If refresh produced a user, go home;
      // if not, fall back to /login.
      const ok = (() => {
        try {
          const raw = localStorage.getItem('pst-auth-user');
          return !!raw;
        } catch {
          return false;
        }
      })();
      navigate(ok ? '/' : '/login', { replace: true });
    })();

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 160px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 16px',
        color: 'var(--fg-secondary)',
        fontSize: 14,
      }}
    >
      {status}
    </div>
  );
}
