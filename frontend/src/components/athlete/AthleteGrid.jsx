import { Link } from 'react-router-dom';
import { getSportConfig } from '../../utils/sportConfig';

/**
 * AthleteGrid — minimal stub by Agent 1.
 * Renders a responsive grid of athlete cards using inline styles + CSS vars.
 */
export default function AthleteGrid({ athletes = [] }) {
  if (!athletes.length) {
    return (
      <div
        style={{
          padding: '48px 16px',
          textAlign: 'center',
          color: 'var(--fg-tertiary)',
          background: 'var(--bg-surface)',
          border: '1px dashed var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          fontSize: 14,
        }}
      >
        No athletes match your filters yet.
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: 16,
      }}
    >
      {athletes.map((a) => {
        const id = a.athlete_id || a.id;
        const name = a.user?.full_name || `${a.user?.first_name || a.first_name || ''} ${a.user?.last_name || a.last_name || ''}`.trim() || 'Athlete';
        const cfg = getSportConfig(a.primary_sport?.code || a.sport);
        const team = a.current_team?.name || a.team || '—';
        const pos  = a.primary_position?.name || a.position || '';
        const rating = a.overall_rating;

        return (
          <Link
            key={id || name}
            to={id ? `/athletes/${id}` : '#'}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
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
              {rating != null && (
                <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--fg-primary)' }}>
                  {rating}
                </span>
              )}
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--fg-primary)', lineHeight: 1.2 }}>
              {name}
            </div>
            <div style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>
              {pos && <span>{pos}</span>}{pos && team ? <span> · </span> : null}
              {team && <span>{team}</span>}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
