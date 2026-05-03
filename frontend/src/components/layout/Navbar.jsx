import { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, X, Sun, Moon, LogIn, LogOut, UserCircle, Trophy } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const NAV_LINKS = [
  { to: '/',          label: 'Dashboard' },
  { to: '/discover',  label: 'Athletes' },
  { to: '/prospects', label: 'Prospects' },
  { to: '/compare',   label: 'Compare' },
];

const linkStyle = (active) => ({
  padding: '8px 14px',
  borderRadius: 'var(--radius-md)',
  fontSize: 14,
  fontWeight: 500,
  color: active ? '#fff' : 'var(--fg-secondary)',
  background: active ? 'var(--orange-500)' : 'transparent',
  textDecoration: 'none',
  transition: 'background-color var(--transition), color var(--transition)',
  whiteSpace: 'nowrap',
});

const iconBtnStyle = {
  background: 'transparent',
  border: '1px solid var(--border-default)',
  color: 'var(--fg-secondary)',
  padding: 8,
  borderRadius: 'var(--radius-md)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  transition: 'border-color var(--transition), color var(--transition)',
};

export default function Navbar({ theme = 'dark', toggleTheme = () => {} }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, login, logout } = useAuth();

  return (
    <header
      style={{
        background: 'var(--bg-nav)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'saturate(140%) blur(6px)',
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: '0 auto',
          padding: '12px clamp(16px, 4vw, 32px)',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: 'var(--fg-primary)',
            textDecoration: 'none',
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--orange-500) 0%, var(--steel-500) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <Trophy size={18} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 20,
                fontWeight: 700,
                color: 'var(--fg-primary)',
              }}
            >
              ProsportsTalents
            </span>
            <span style={{ fontSize: 11, color: 'var(--fg-tertiary)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Talent Agency
            </span>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="pst-nav-desktop" style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 12 }}>
          {NAV_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'} style={({ isActive }) => linkStyle(isActive)}>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            title={theme === 'dark' ? 'Switch to light' : 'Switch to dark'}
            style={iconBtnStyle}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {user ? (
            <div className="pst-nav-user" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--fg-secondary)', fontSize: 13 }}>
                <UserCircle size={18} />
                <span>{user.full_name || user.first_name || user.email || 'User'}</span>
              </span>
              <button
                type="button"
                onClick={logout}
                style={{ ...iconBtnStyle, padding: '8px 12px', display: 'inline-flex', gap: 6 }}
                title="Sign out"
              >
                <LogOut size={14} />
                <span style={{ fontSize: 13 }}>Sign out</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => login('google')}
              style={{
                background: 'var(--orange-500)',
                color: '#fff',
                border: 'none',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                cursor: 'pointer',
                transition: 'opacity var(--transition)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.88')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              <LogIn size={14} />
              Sign in
            </button>
          )}

          <button
            type="button"
            className="pst-nav-mobile-toggle"
            aria-label="Open menu"
            onClick={() => setMobileOpen((o) => !o)}
            style={{ ...iconBtnStyle, display: 'none' }}
          >
            {mobileOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <nav
          className="pst-nav-mobile"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            padding: '8px 16px 16px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'var(--bg-nav)',
          }}
        >
          {NAV_LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              onClick={() => setMobileOpen(false)}
              style={({ isActive }) => ({ ...linkStyle(isActive), padding: '10px 14px' })}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      )}

      {/* Tiny inline responsive overrides — no Tailwind config required */}
      <style>{`
        @media (max-width: 768px) {
          .pst-nav-desktop { display: none !important; }
          .pst-nav-user span:last-child { display: none; }
          .pst-nav-mobile-toggle { display: inline-flex !important; }
        }
      `}</style>
    </header>
  );
}
