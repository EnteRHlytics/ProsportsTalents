import { useNavigate, useParams, Link } from 'react-router-dom';
import { Edit3, Trash2, ArrowLeft, GraduationCap, Calendar, Hash } from 'lucide-react';
import PageWrapper from '../components/layout/PageWrapper';
import EmptyState from '../components/common/EmptyState';
import ErrorBanner from '../components/common/ErrorBanner';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import SkillRadar from '../components/charts/SkillRadar';
import { getSportConfig } from '../utils/sportConfig';
import useApi, { apiFetch } from '../hooks/useApi';

function fullName(p) {
  return p?.user?.full_name
    || `${p?.user?.first_name || p?.first_name || ''} ${p?.user?.last_name || p?.last_name || ''}`.trim()
    || p?.name
    || 'Prospect';
}

export default function ProspectProfile() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: prospect, error, loading, refetch } = useApi(`/prospects/${id}`);
  const skillsQuery = useApi(`/prospects/${id}/skills`);

  const handleDelete = async () => {
    if (!window.confirm('Delete this prospect?')) return;
    try {
      await apiFetch(`/prospects/${id}`, { method: 'DELETE' });
      navigate('/prospects');
    } catch (e) {
      alert(e.message || 'Failed to delete prospect');
    }
  };

  if (loading) {
    return <PageWrapper><LoadingSpinner /></PageWrapper>;
  }

  if (error) {
    return (
      <PageWrapper>
        <ErrorBanner message={error.message || 'Failed to load prospect'} onRetry={() => refetch()} />
        <div style={{ marginTop: 12 }}>
          <Link to="/prospects" style={{ color: 'var(--orange-500)', fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <ArrowLeft size={14} /> Back to prospects
          </Link>
        </div>
      </PageWrapper>
    );
  }

  if (!prospect) {
    return (
      <PageWrapper>
        <EmptyState
          title="Prospect not found"
          description="This prospect may have been removed, or the prospects backend isn't online yet."
          action={
            <Link
              to="/prospects"
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
              <ArrowLeft size={14} /> Back to prospects
            </Link>
          }
        />
      </PageWrapper>
    );
  }

  const cfg = getSportConfig(prospect.primary_sport?.code || prospect.sport);
  const skills = skillsQuery.data || [];

  return (
    <PageWrapper>
      <div style={{ marginBottom: 12 }}>
        <Link to="/prospects" style={{ color: 'var(--fg-tertiary)', fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <ArrowLeft size={12} /> All prospects
        </Link>
      </div>

      {/* Hero */}
      <div
        style={{
          marginBottom: 24,
          borderRadius: 'var(--radius-xl)',
          background: `linear-gradient(135deg, ${cfg.color} 0%, var(--navy-700) 80%)`,
          padding: 24,
          color: '#fff',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                padding: '3px 10px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(0,0,0,0.25)',
              }}
            >
              {cfg.code} Prospect{prospect.position ? ` · ${prospect.position}` : ''}
            </span>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 38, margin: '8px 0 6px', color: '#fff' }}>
              {fullName(prospect)}
            </h1>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, fontSize: 13, opacity: 0.9 }}>
              {prospect.school && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <GraduationCap size={13} /> {prospect.school}
                </span>
              )}
              {(prospect.draft_year || prospect.draft_eligible_year) && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Calendar size={13} /> Draft {prospect.draft_year || prospect.draft_eligible_year}
                </span>
              )}
              {prospect.height && <span>Height: {prospect.height}</span>}
              {prospect.weight && <span>Weight: {prospect.weight}</span>}
              {prospect.jersey_number && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Hash size={13} /> {prospect.jersey_number}
                </span>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            {prospect.scout_grade != null && (
              <div
                style={{
                  background: 'rgba(0,0,0,0.30)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 14px',
                  textAlign: 'center',
                  minWidth: 80,
                }}
              >
                <div style={{ fontSize: 10, opacity: 0.75, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                  Scout
                </div>
                <div style={{ fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{prospect.scout_grade}</div>
              </div>
            )}
            <Link
              to={`/prospects/${id}/edit`}
              style={{
                background: 'rgba(255,255,255,0.18)',
                color: '#fff',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Edit3 size={14} /> Edit
            </Link>
            <button
              type="button"
              onClick={handleDelete}
              style={{
                background: 'rgba(0,0,0,0.30)',
                color: '#fff',
                border: 'none',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
        </div>
        {prospect.bio && (
          <p style={{ marginTop: 14, maxWidth: 720, fontSize: 14, lineHeight: 1.6, opacity: 0.92 }}>
            {prospect.bio}
          </p>
        )}
      </div>

      {/* Body grid */}
      <div
        className="pst-prospect-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 2fr)',
          gap: 20,
          alignItems: 'start',
        }}
      >
        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: 16,
          }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, margin: '0 0 12px', color: 'var(--fg-primary)' }}>
            Scouting Notes
          </h2>
          {prospect.scout_notes ? (
            <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap', margin: 0 }}>
              {prospect.scout_notes}
            </p>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--fg-tertiary)', margin: 0 }}>
              No scouting notes recorded yet.
            </p>
          )}

          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, color: 'var(--fg-secondary)' }}>
            {prospect.agent && <div><strong style={{ color: 'var(--fg-primary)' }}>Agent:</strong> {prospect.agent}</div>}
            {prospect.nationality && <div><strong style={{ color: 'var(--fg-primary)' }}>Nationality:</strong> {prospect.nationality}</div>}
            {prospect.date_of_birth && <div><strong style={{ color: 'var(--fg-primary)' }}>DOB:</strong> {prospect.date_of_birth}</div>}
          </div>
        </section>

        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: 16,
          }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, margin: '0 0 12px', color: 'var(--fg-primary)' }}>
            Skills
          </h2>
          {skillsQuery.loading ? (
            <LoadingSpinner />
          ) : skills.length ? (
            <SkillRadar skills={skills} color={cfg.color} label={fullName(prospect)} />
          ) : (
            <p style={{ fontSize: 13, color: 'var(--fg-tertiary)', margin: 0 }}>
              No skills tracked for this prospect yet.
            </p>
          )}
        </section>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .pst-prospect-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </PageWrapper>
  );
}
