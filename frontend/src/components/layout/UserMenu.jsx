import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronDown, LogOut, User, UserCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

/**
 * UserMenu — avatar/name dropdown shown when a user is authenticated.
 *
 * Items: Profile (link to /profile or /), Sign out (calls auth.logout()).
 */
export default function UserMenu() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const user = auth?.user;
  if (!user) return null;

  const displayName = user.full_name || user.first_name || user.email || user.username || 'User';
  const initials = displayName
    .split(/\s+/)
    .map((s) => s[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

  async function handleSignOut() {
    setOpen(false);
    try { await auth.logout(); } catch { /* ignore */ }
    navigate('/login');
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 10px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          background: 'transparent',
          color: 'var(--fg-secondary)',
          cursor: 'pointer',
          fontSize: 13,
        }}
      >
        <span
          aria-hidden="true"
          style={{
            width: 26,
            height: 26,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--orange-500) 0%, var(--steel-500) 100%)',
            color: '#fff',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          {initials || <UserCircle size={16} />}
        </span>
        <span className="pst-user-name" style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {displayName}
        </span>
        <ChevronDown size={14} />
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            minWidth: 200,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
            zIndex: 60,
            overflow: 'hidden',
          }}
        >
          <Link
            to="/"
            role="menuitem"
            onClick={() => setOpen(false)}
            style={menuItemStyle}
          >
            <User size={14} />
            <span>Profile</span>
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            style={{ ...menuItemStyle, width: '100%', border: 'none', background: 'transparent', cursor: 'pointer' }}
          >
            <LogOut size={14} />
            <span>Sign out</span>
          </button>
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .pst-user-name { display: none; }
        }
      `}</style>
    </div>
  );
}

const menuItemStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '10px 12px',
  fontSize: 13,
  color: 'var(--fg-primary)',
  textDecoration: 'none',
  textAlign: 'left',
  fontFamily: 'var(--font-body)',
};
