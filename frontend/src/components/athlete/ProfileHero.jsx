import { Edit3, Trash2, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getSportConfig } from '../../utils/sportConfig';

/**
 * ProfileHero — minimal stub by Agent 1.
 */
export default function ProfileHero({ athlete, onDelete }) {
  if (!athlete) return null;
  const id = athlete.athlete_id || athlete.id;
  const cfg = getSportConfig(athlete.primary_sport?.code);
  const fullName = athlete.user?.full_name
    || `${athlete.user?.first_name || ''} ${athlete.user?.last_name || ''}`.trim()
    || 'Athlete';

  return (
    <div
      style={{
        position: 'relative',
        marginBottom: 24,
        borderRadius: 'var(--radius-xl)',
        background: `linear-gradient(135deg, ${cfg.color} 0%, var(--navy-700) 80%)`,
        padding: 24,
        color: '#fff',
        overflow: 'hidden',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between' }}>
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
            {cfg.code} {athlete.primary_position?.name ? `· ${athlete.primary_position.name}` : ''}
          </span>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 40, margin: '8px 0 6px', color: '#fff' }}>
            {fullName}
          </h1>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, fontSize: 13, opacity: 0.85 }}>
            {athlete.current_team?.name && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <MapPin size={13} /> {athlete.current_team.name}
              </span>
            )}
            {athlete.nationality && <span>{athlete.nationality}</span>}
            {athlete.jersey_number && <span>#{athlete.jersey_number}</span>}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {athlete.overall_rating != null && (
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
                Rating
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{athlete.overall_rating}</div>
            </div>
          )}
          {id && (
            <Link
              to={`/athletes/${id}/edit`}
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
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              style={{
                background: 'rgba(0,0,0,0.30)',
                color: '#fff',
                border: 'none',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                cursor: 'pointer',
              }}
            >
              <Trash2 size={14} /> Delete
            </button>
          )}
        </div>
      </div>

      {athlete.bio && (
        <p style={{ marginTop: 14, maxWidth: 720, fontSize: 14, lineHeight: 1.6, opacity: 0.92 }}>
          {athlete.bio}
        </p>
      )}
    </div>
  );
}
