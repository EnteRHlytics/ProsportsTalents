import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Github, AtSign, LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/**
 * Login view.
 *
 * Renders three SSO buttons (Google, GitHub, Microsoft) plus a fallback
 * username/password form posting to the existing local auth endpoint
 * (``POST /auth/login``). On successful local login, the user is
 * redirected to ``/`` after refreshing the auth context.
 */
export default function Login() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const ssoProviders = [
    { id: 'google',    label: 'Continue with Google',    Icon: Mail },
    { id: 'github',    label: 'Continue with GitHub',    Icon: Github },
    { id: 'microsoft', label: 'Continue with Microsoft', Icon: AtSign },
  ];

  async function handleLocalLogin(e) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password, username: email }),
      });
      if (!res.ok) {
        let msg = `Sign-in failed (${res.status})`;
        try {
          const body = await res.json();
          if (body?.message) msg = body.message;
          else if (body?.error) msg = body.error;
        } catch { /* ignore */ }
        setFormError(msg);
        return;
      }
      if (auth?.refresh) await auth.refresh();
      navigate('/');
    } catch (err) {
      setFormError(err?.message || 'Sign-in failed');
    } finally {
      setSubmitting(false);
    }
  }

  const cardStyle = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg, 12px)',
    boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
    padding: 28,
    width: '100%',
    maxWidth: 420,
  };

  const ssoBtnStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    width: '100%',
    padding: '10px 14px',
    borderRadius: 'var(--radius-md, 6px)',
    border: '1px solid var(--border-default)',
    background: 'var(--bg-surface)',
    color: 'var(--fg-primary)',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'var(--font-body)',
    transition: 'border-color var(--transition), background-color var(--transition)',
  };

  const inputStyle = {
    width: '100%',
    padding: '9px 12px',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-md, 6px)',
    background: 'var(--bg-surface)',
    color: 'var(--fg-primary)',
    fontSize: 14,
    fontFamily: 'var(--font-body)',
  };

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 160px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 16px',
      }}
    >
      <div style={cardStyle} role="region" aria-label="Sign in">
        <h1
          style={{
            fontSize: 26,
            fontWeight: 700,
            margin: '0 0 6px',
            color: 'var(--fg-primary)',
            fontFamily: 'var(--font-display)',
          }}
        >
          Sign in
        </h1>
        <p style={{ fontSize: 13, color: 'var(--fg-tertiary)', margin: '0 0 20px' }}>
          Use a single sign-on provider or your account credentials.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 18 }}>
          {ssoProviders.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              data-provider={id}
              aria-label={label}
              onClick={() => auth.login(id)}
              style={ssoBtnStyle}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--orange-500)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-default)')}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            margin: '14px 0',
            color: 'var(--fg-tertiary)',
            fontSize: 12,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          <span style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
          <span>or</span>
          <span style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
        </div>

        <form onSubmit={handleLocalLogin} aria-label="Sign in with email and password">
          <label style={{ display: 'block', fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 4 }}>
            Email or username
          </label>
          <input
            type="text"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ ...inputStyle, marginBottom: 12 }}
            required
          />
          <label style={{ display: 'block', fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 4 }}>
            Password
          </label>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ ...inputStyle, marginBottom: 14 }}
            required
          />
          {formError && (
            <div
              role="alert"
              style={{
                padding: '8px 10px',
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.35)',
                color: '#fca5a5',
                borderRadius: 'var(--radius-md, 6px)',
                fontSize: 12,
                marginBottom: 12,
              }}
            >
              {formError}
            </div>
          )}
          <button
            type="submit"
            disabled={submitting}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              width: '100%',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md, 6px)',
              background: 'var(--orange-500)',
              color: '#fff',
              border: 'none',
              fontSize: 14,
              fontWeight: 600,
              cursor: submitting ? 'progress' : 'pointer',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            <LogIn size={14} />
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
