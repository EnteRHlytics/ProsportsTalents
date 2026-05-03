import { Link } from 'react-router-dom';
import { Users, Star, Trophy, Heart, Upload, BarChart3, ChevronRight, Sparkles } from 'lucide-react';
import PageWrapper from '../components/layout/PageWrapper';
import { SkeletonGrid } from '../components/common/SkeletonCard';
import EmptyState from '../components/common/EmptyState';
import ErrorBanner from '../components/common/ErrorBanner';
import AthleteGrid from '../components/athlete/AthleteGrid';
import { getSportConfig } from '../utils/sportConfig';
import useApi from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';

function KpiCard({ icon: Icon, label, value, hint, color = 'var(--orange-500)' }) {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: 18,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        boxShadow: 'var(--shadow-xs)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--fg-tertiary)' }}>
          {label}
        </span>
        <span
          style={{
            background: `${color}22`,
            color,
            borderRadius: 'var(--radius-sm)',
            padding: 6,
            display: 'inline-flex',
          }}
        >
          <Icon size={16} />
        </span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--fg-primary)', lineHeight: 1.1 }}>
        {value ?? '—'}
      </div>
      {hint && (
        <div style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>{hint}</div>
      )}
    </div>
  );
}

function QuickLink({ to, icon: Icon, label, description, color = 'var(--orange-500)' }) {
  return (
    <Link
      to={to}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: 14,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        textDecoration: 'none',
        color: 'var(--fg-primary)',
        transition: 'border-color var(--transition), transform var(--transition)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-strong)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-subtle)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <span
        style={{
          background: `${color}22`,
          color,
          borderRadius: 'var(--radius-md)',
          width: 36,
          height: 36,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Icon size={18} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg-primary)' }}>{label}</div>
        {description && <div style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>{description}</div>}
      </div>
      <ChevronRight size={16} color="var(--fg-tertiary)" />
    </Link>
  );
}

function RankingsList({ athletes }) {
  if (!athletes?.length) {
    return <EmptyState compact title="No rankings yet" description="Top athletes will appear here once stats are loaded." />;
  }
  return (
    <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {athletes.slice(0, 8).map((a, idx) => {
        const id = a.athlete_id || a.id;
        const cfg = getSportConfig(a.primary_sport?.code || a.sport);
        const name = a.user?.full_name
          || `${a.user?.first_name || a.first_name || ''} ${a.user?.last_name || a.last_name || ''}`.trim()
          || 'Athlete';
        return (
          <li key={id || idx}>
            <Link
              to={id ? `/athletes/${id}` : '#'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                background: 'var(--bg-surface-alt)',
                borderRadius: 'var(--radius-md)',
                textDecoration: 'none',
                color: 'var(--fg-primary)',
                fontSize: 13,
              }}
            >
              <span
                style={{
                  width: 24,
                  height: 24,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--navy-700)',
                  color: 'var(--fg-secondary)',
                  fontSize: 11,
                  fontWeight: 700,
                }}
              >
                {idx + 1}
              </span>
              <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {name}
              </span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: '#fff',
                  background: cfg.color,
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                {cfg.code}
              </span>
              {a.overall_rating != null && (
                <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--fg-primary)', minWidth: 28, textAlign: 'right' }}>
                  {a.overall_rating}
                </span>
              )}
            </Link>
          </li>
        );
      })}
    </ol>
  );
}

export default function Dashboard() {
  const { user } = useAuth();

  // KPI-friendly endpoints. Use ?per_page=1 to get a "total" cheaply if backend supports it.
  const totalQuery    = useApi('/athletes/search?per_page=1');
  const featuredQuery = useApi('/athletes/search?featured=true&per_page=8');
  const topQuery      = useApi('/athletes/search?sort=-overall_rating&per_page=8');

  const totalAthletes = totalQuery.data?.total
    ?? (Array.isArray(totalQuery.data?.results) ? totalQuery.data.results.length : null);
  const featured = featuredQuery.data?.results || (Array.isArray(featuredQuery.data) ? featuredQuery.data : []);
  const top      = topQuery.data?.results || (Array.isArray(topQuery.data) ? topQuery.data : []);
  const featuredCount = featured.length;
  const topRated      = top[0];

  const error = totalQuery.error || featuredQuery.error || topQuery.error;
  const loading = totalQuery.loading && featuredQuery.loading && topQuery.loading;

  return (
    <PageWrapper>
      {/* Hero */}
      <div
        style={{
          marginBottom: 24,
          padding: '24px 28px',
          borderRadius: 'var(--radius-xl)',
          background: 'linear-gradient(135deg, var(--navy-700) 0%, var(--navy-900) 60%, var(--steel-500) 130%)',
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--orange-300)' }}>
          <Sparkles size={12} /> Pro Sports Talent Agency
        </span>
        <h1 style={{ fontFamily: 'var(--font-display)', margin: '8px 0 4px', fontSize: 'clamp(28px, 4vw, 40px)', color: '#fff' }}>
          Welcome{user?.first_name ? `, ${user.first_name}` : ' back'}
        </h1>
        <p style={{ margin: 0, fontSize: 14, opacity: 0.85, maxWidth: 640 }}>
          Manage your roster, showcase prospects to teams and sponsors, and track performance across the NBA, NFL, MLB, NHL and more.
        </p>
      </div>

      {error && !loading && (
        <div style={{ marginBottom: 16 }}>
          <ErrorBanner
            message="We couldn't load some dashboard data. Showing what we have."
            onRetry={() => {
              totalQuery.refetch();
              featuredQuery.refetch();
              topQuery.refetch();
            }}
            compact
          />
        </div>
      )}

      {/* KPI cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 14,
          marginBottom: 28,
        }}
      >
        <KpiCard icon={Users}  label="Total Athletes"    value={totalAthletes}  hint="Across all sports" color="var(--steel-500)" />
        <KpiCard icon={Star}   label="Featured"          value={featuredCount}  hint="On the showcase reel" color="var(--orange-500)" />
        <KpiCard
          icon={Trophy}
          label="Top Ranked"
          value={topRated ? (topRated.user?.full_name || `${topRated.user?.first_name || ''} ${topRated.user?.last_name || ''}`.trim()) : '—'}
          hint={topRated?.overall_rating != null ? `Rating ${topRated.overall_rating}` : 'No data yet'}
          color="var(--green-500)"
        />
        <KpiCard icon={Heart}  label="Client Satisfaction" value="92%" hint="Placeholder · NPS rolling 30d" color="var(--orange-300)" />
      </div>

      {/* Two-column layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
          gap: 20,
          alignItems: 'start',
        }}
        className="pst-dashboard-grid"
      >
        {/* Featured athletes */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 24, color: 'var(--fg-primary)', margin: 0 }}>
              Featured Athletes
            </h2>
            <Link
              to="/discover"
              style={{ fontSize: 12, color: 'var(--fg-tertiary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              View all <ChevronRight size={14} />
            </Link>
          </div>
          {featuredQuery.loading
            ? <SkeletonGrid count={4} />
            : featured.length
              ? <AthleteGrid athletes={featured} />
              : <EmptyState
                  title="No featured athletes yet"
                  description="Mark athletes as featured to surface them on the homepage."
                  action={
                    <Link
                      to="/athletes/new"
                      style={{
                        background: 'var(--orange-500)',
                        color: '#fff',
                        padding: '8px 14px',
                        borderRadius: 'var(--radius-md)',
                        fontSize: 13,
                        textDecoration: 'none',
                      }}
                    >
                      Add an athlete
                    </Link>
                  }
                />
          }
        </section>

        {/* Right column */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <section>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--fg-primary)', margin: '0 0 10px' }}>
              Top Rankings
            </h2>
            {topQuery.loading
              ? <SkeletonGrid count={3} />
              : <RankingsList athletes={top} />}
          </section>

          <section>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--fg-primary)', margin: '0 0 10px' }}>
              Quick Actions
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <QuickLink
                to="/athletes/new"
                icon={Upload}
                label="Upload Media"
                description="Add an athlete + media reel"
                color="var(--orange-500)"
              />
              <QuickLink
                to="/compare"
                icon={BarChart3}
                label="View Analytics"
                description="Compare athletes side-by-side"
                color="var(--steel-500)"
              />
              <QuickLink
                to="/prospects/new"
                icon={Sparkles}
                label="Add Prospect"
                description="Track a pre-signing athlete"
                color="var(--green-500)"
              />
            </div>
          </section>
        </aside>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .pst-dashboard-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </PageWrapper>
  );
}
