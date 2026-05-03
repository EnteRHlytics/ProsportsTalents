import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import PageWrapper from '../components/layout/PageWrapper';
import EmptyState from '../components/common/EmptyState';
import ErrorBanner from '../components/common/ErrorBanner';
import { SkeletonGrid } from '../components/common/SkeletonCard';
import SportFilterTabs from '../components/athlete/SportFilterTabs';
import { getSportConfig } from '../utils/sportConfig';
import useApi from '../hooks/useApi';

function fullName(p) {
  return p?.user?.full_name
    || `${p?.user?.first_name || p?.first_name || ''} ${p?.user?.last_name || p?.last_name || ''}`.trim()
    || p?.name
    || 'Prospect';
}

function ProspectCard({ p }) {
  const id = p.prospect_id || p.id;
  const cfg = getSportConfig(p.primary_sport?.code || p.sport);
  const draftEligible = p.draft_year || p.draft_eligible_year;
  return (
    <Link
      to={id ? `/prospects/${id}` : '#'}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        padding: 16,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        textDecoration: 'none',
        color: 'var(--fg-primary)',
        transition: 'transform var(--transition), border-color var(--transition), box-shadow var(--transition)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.borderColor = 'var(--border-strong)';
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.borderColor = 'var(--border-subtle)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            color: '#fff',
            padding: '3px 8px',
            borderRadius: 'var(--radius-sm)',
            background: cfg.color,
          }}
        >
          {cfg.code}
        </span>
        {draftEligible && (
          <span style={{ fontSize: 11, color: 'var(--fg-tertiary)' }}>Draft {draftEligible}</span>
        )}
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--fg-primary)', lineHeight: 1.2 }}>
        {fullName(p)}
      </div>
      <div style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>
        {p.school || p.team || ''}
        {p.position ? `${p.school || p.team ? ' · ' : ''}${p.position}` : ''}
      </div>
      {p.scout_grade != null && (
        <div style={{ fontSize: 11, color: 'var(--fg-secondary)', marginTop: 2 }}>
          Scout grade: <strong style={{ color: 'var(--fg-primary)' }}>{p.scout_grade}</strong>
        </div>
      )}
    </Link>
  );
}

export default function ProspectList() {
  const [sport, setSport] = useState('ALL');
  const [q, setQ] = useState('');

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (sport && sport !== 'ALL') params.append('sport', sport);
    const s = params.toString();
    return s ? `?${s}` : '';
  }, [q, sport]);

  const { data, error, loading, refetch } = useApi(`/prospects${queryString}`, { deps: [queryString] });

  // Backend may not exist yet — useApi treats 404 as null-data (emptyOn404)
  const prospects = Array.isArray(data) ? data : (data?.results || data?.items || []);

  return (
    <PageWrapper>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <span style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--orange-500)' }}>
            Pre-Signing
          </span>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(28px, 4vw, 38px)', margin: '4px 0 6px', color: 'var(--fg-primary)' }}>
            Prospects
          </h1>
          <p style={{ color: 'var(--fg-tertiary)', fontSize: 14, margin: 0 }}>
            Track athletes before they sign. Light schema — name, sport, school, scout notes.
          </p>
        </div>
        <Link
          to="/prospects/new"
          style={{
            background: 'var(--orange-500)',
            color: '#fff',
            padding: '10px 16px',
            borderRadius: 'var(--radius-md)',
            fontSize: 14,
            fontWeight: 600,
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Plus size={16} /> New Prospect
        </Link>
      </div>

      <SportFilterTabs selected={sport} onChange={setSport} />

      <div style={{ position: 'relative', marginBottom: 18, maxWidth: 480 }}>
        <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--fg-tertiary)' }} />
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search prospects…"
          style={{
            width: '100%',
            padding: '9px 12px 9px 34px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            fontSize: 13,
            color: 'var(--fg-primary)',
            outline: 'none',
          }}
        />
      </div>

      {error && (
        <div style={{ marginBottom: 12 }}>
          <ErrorBanner message={error.message} onRetry={() => refetch()} />
        </div>
      )}

      {loading ? (
        <SkeletonGrid count={6} />
      ) : prospects.length === 0 ? (
        <EmptyState
          title="No prospects yet"
          description="The /api/prospects endpoint returned no data. Add a prospect or wait for the backend to ship."
          action={
            <Link
              to="/prospects/new"
              style={{
                background: 'var(--orange-500)',
                color: '#fff',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Plus size={14} /> Add prospect
            </Link>
          }
        />
      ) : (
        <>
          <div style={{ fontSize: 13, color: 'var(--fg-tertiary)', marginBottom: 12 }}>
            {prospects.length} prospect{prospects.length !== 1 ? 's' : ''}
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: 16,
            }}
          >
            {prospects.map((p) => (
              <ProspectCard key={p.prospect_id || p.id || fullName(p)} p={p} />
            ))}
          </div>
        </>
      )}
    </PageWrapper>
  );
}
