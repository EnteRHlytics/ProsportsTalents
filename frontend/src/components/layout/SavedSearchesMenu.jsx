import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, ChevronDown } from 'lucide-react';
import useApi from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';

/**
 * SavedSearchesMenu — Navbar dropdown listing the user's saved searches.
 *
 * Each entry links to ``/discover?<params>`` so clicking it re-runs the
 * search with the saved filters. Hidden when the user is not signed in.
 */
export default function SavedSearchesMenu() {
  const auth = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Only fetch when signed in to avoid a 401 round trip for guests.
  const { data, loading, error, refetch } = useApi('/api/saved-searches', {
    skip: !auth?.user,
  });

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  // Refresh when opened.
  useEffect(() => {
    if (open && auth?.user) refetch?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!auth?.user) return null;

  const items = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : [];

  function buildLink(s) {
    const p = s.params || {};
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(p)) {
      if (v == null || v === '') continue;
      sp.set(k, String(v));
    }
    return `/discover${sp.toString() ? `?${sp.toString()}` : ''}`;
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
          gap: 6,
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          background: 'transparent',
          color: 'var(--fg-secondary)',
          cursor: 'pointer',
          fontSize: 13,
        }}
        title="Saved searches"
      >
        <Bookmark size={14} />
        <span className="pst-saved-label">Saved</span>
        <ChevronDown size={12} />
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            minWidth: 240,
            maxHeight: 360,
            overflowY: 'auto',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
            zIndex: 60,
          }}
        >
          <div
            style={{
              padding: '8px 12px',
              fontSize: 11,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--fg-tertiary)',
              borderBottom: '1px solid var(--border-subtle)',
            }}
          >
            Saved searches
          </div>

          {loading && (
            <div style={{ padding: 12, fontSize: 12, color: 'var(--fg-tertiary)' }}>
              Loading...
            </div>
          )}
          {error && !loading && (
            <div style={{ padding: 12, fontSize: 12, color: '#fca5a5' }}>
              {error?.message || 'Failed to load saved searches'}
            </div>
          )}
          {!loading && !error && items.length === 0 && (
            <div style={{ padding: 12, fontSize: 12, color: 'var(--fg-tertiary)' }}>
              No saved searches yet.
            </div>
          )}
          {!loading && items.length > 0 && (
            <ul role="none" style={{ listStyle: 'none', margin: 0, padding: 4 }}>
              {items.map((s) => (
                <li key={s.id} role="none">
                  <Link
                    to={buildLink(s)}
                    role="menuitem"
                    onClick={() => setOpen(false)}
                    style={{
                      display: 'block',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm, 4px)',
                      fontSize: 13,
                      color: 'var(--fg-primary)',
                      textDecoration: 'none',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-hover, rgba(255,255,255,0.04))')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    title={s.name}
                  >
                    {s.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <div style={{ borderTop: '1px solid var(--border-subtle)', padding: 6 }}>
            <Link
              to="/discover"
              onClick={() => setOpen(false)}
              style={{
                display: 'block',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm, 4px)',
                fontSize: 12,
                color: 'var(--orange-400, var(--orange-500))',
                textDecoration: 'none',
              }}
            >
              Manage in Discover
            </Link>
          </div>
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .pst-saved-label { display: none; }
        }
      `}</style>
    </div>
  );
}
