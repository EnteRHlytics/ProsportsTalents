import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity as ActivityIcon, RefreshCw, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import PageWrapper from '../components/layout/PageWrapper';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';

/**
 * Admin activity log view.
 *
 * Backend: GET /api/activity?user_id=&limit=&since= (admin-only).
 * Returns { items: ActivityLog[], count, limit }.
 *
 * The route is gated client-side by `auth.hasRole('admin' | 'agency_admin')`.
 * The backend re-checks the role server-side (returning 403 otherwise).
 */
export default function AdminActivity() {
  const auth = useAuth();
  const isAdmin = useMemo(
    () => auth?.hasRole?.(['admin', 'agency_admin']) || false,
    [auth],
  );

  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [userId, setUserId] = useState('');
  const [since, setSince] = useState('');
  const [limit, setLimit] = useState(50);
  const [appliedQuery, setAppliedQuery] = useState({ userId: '', since: '', limit: 50 });

  const fetchActivity = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const sp = new URLSearchParams();
      if (appliedQuery.userId) sp.set('user_id', appliedQuery.userId);
      if (appliedQuery.since) sp.set('since', appliedQuery.since);
      if (appliedQuery.limit) sp.set('limit', String(appliedQuery.limit));
      const res = await fetch(`/api/activity?${sp.toString()}`, { credentials: 'include' });
      if (res.status === 401 || res.status === 403) {
        setItems([]);
        setError('You do not have permission to view this page.');
        return;
      }
      if (!res.ok) {
        setError(`Failed to load activity (${res.status})`);
        return;
      }
      const body = await res.json();
      const list = Array.isArray(body?.items) ? body.items : Array.isArray(body) ? body : [];
      setItems(list);
      setCount(body?.count ?? list.length);
    } catch (e) {
      setError(e?.message || 'Failed to load activity');
    } finally {
      setLoading(false);
    }
  }, [appliedQuery]);

  useEffect(() => {
    if (!isAdmin) return;
    fetchActivity();
  }, [isAdmin, fetchActivity]);

  if (!isAdmin) {
    return (
      <PageWrapper>
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg, 12px)',
            padding: 28,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            color: 'var(--fg-primary)',
          }}
          role="alert"
        >
          <ShieldAlert size={20} color="#f59e0b" />
          <div>
            <div style={{ fontWeight: 600 }}>Access denied</div>
            <div style={{ fontSize: 13, color: 'var(--fg-tertiary)' }}>
              You need an admin role to view the activity log.
            </div>
          </div>
        </div>
      </PageWrapper>
    );
  }

  function applyFilters(e) {
    e.preventDefault();
    setAppliedQuery({ userId, since, limit });
  }

  function nextPage() {
    setLimit((n) => n + 50);
    setAppliedQuery((q) => ({ ...q, limit: q.limit + 50 }));
  }

  const tableCellStyle = {
    padding: '8px 10px',
    fontSize: 13,
    color: 'var(--fg-secondary)',
    borderBottom: '1px solid var(--border-subtle)',
    textAlign: 'left',
    verticalAlign: 'top',
  };
  const headerCellStyle = {
    ...tableCellStyle,
    color: 'var(--fg-tertiary)',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    fontWeight: 600,
    background: 'var(--bg-surface-alt, var(--bg-surface))',
  };

  return (
    <PageWrapper>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 30,
              margin: 0,
              fontFamily: 'var(--font-display)',
              color: 'var(--fg-primary)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <ActivityIcon size={22} color="var(--orange-500)" />
            Activity Log
          </h1>
          <p style={{ color: 'var(--fg-tertiary)', fontSize: 14, margin: '6px 0 0' }}>
            Showing {count} most recent {count === 1 ? 'entry' : 'entries'}.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchActivity}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 12px',
            borderRadius: 'var(--radius-md, 6px)',
            border: '1px solid var(--border-default)',
            background: 'var(--bg-surface)',
            color: 'var(--fg-primary)',
            fontSize: 13,
            cursor: 'pointer',
          }}
          aria-label="Refresh"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <form
        onSubmit={applyFilters}
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 10,
          marginBottom: 14,
          alignItems: 'flex-end',
        }}
      >
        <label style={{ display: 'flex', flexDirection: 'column', fontSize: 12, color: 'var(--fg-tertiary)' }}>
          User ID
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Filter by user id"
            style={{
              marginTop: 4,
              padding: '8px 10px',
              borderRadius: 'var(--radius-md, 6px)',
              border: '1px solid var(--border-default)',
              background: 'var(--bg-surface)',
              color: 'var(--fg-primary)',
              fontSize: 13,
              minWidth: 180,
            }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', fontSize: 12, color: 'var(--fg-tertiary)' }}>
          Since
          <input
            type="datetime-local"
            value={since}
            onChange={(e) => setSince(e.target.value)}
            style={{
              marginTop: 4,
              padding: '8px 10px',
              borderRadius: 'var(--radius-md, 6px)',
              border: '1px solid var(--border-default)',
              background: 'var(--bg-surface)',
              color: 'var(--fg-primary)',
              fontSize: 13,
            }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', fontSize: 12, color: 'var(--fg-tertiary)' }}>
          Limit
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{
              marginTop: 4,
              padding: '8px 10px',
              borderRadius: 'var(--radius-md, 6px)',
              border: '1px solid var(--border-default)',
              background: 'var(--bg-surface)',
              color: 'var(--fg-primary)',
              fontSize: 13,
            }}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
        </label>
        <button
          type="submit"
          style={{
            padding: '8px 14px',
            borderRadius: 'var(--radius-md, 6px)',
            background: 'var(--orange-500)',
            color: '#fff',
            border: 'none',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Apply
        </button>
      </form>

      <ErrorMessage message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg, 12px)',
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={headerCellStyle}>Timestamp</th>
                <th style={headerCellStyle}>User</th>
                <th style={headerCellStyle}>Method</th>
                <th style={headerCellStyle}>Path</th>
                <th style={headerCellStyle}>Status</th>
                <th style={headerCellStyle}>IP</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6} style={{ ...tableCellStyle, textAlign: 'center', padding: 20, color: 'var(--fg-tertiary)' }}>
                    No activity entries found.
                  </td>
                </tr>
              ) : (
                items.map((row, idx) => (
                  <tr key={row.id ?? idx}>
                    <td style={tableCellStyle}>{row.created_at || row.timestamp || '-'}</td>
                    <td style={tableCellStyle}>{row.user_id ?? row.user?.id ?? '-'}</td>
                    <td style={tableCellStyle}>{row.method || '-'}</td>
                    <td style={tableCellStyle}>{row.path || row.endpoint || '-'}</td>
                    <td style={tableCellStyle}>{row.status_code ?? row.status ?? '-'}</td>
                    <td style={tableCellStyle}>{row.ip_address || row.ip || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {items.length >= appliedQuery.limit && (
            <div style={{ padding: 12, textAlign: 'center', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                onClick={nextPage}
                style={{
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md, 6px)',
                  border: '1px solid var(--border-default)',
                  background: 'var(--bg-surface)',
                  color: 'var(--fg-primary)',
                  fontSize: 13,
                  cursor: 'pointer',
                }}
              >
                Load more
              </button>
            </div>
          )}
        </div>
      )}
    </PageWrapper>
  );
}
