import { listSports } from '../../utils/sportConfig';

/**
 * SportFilterTabs — minimal stub by Agent 1.
 * Pill-style sport selector. Calls onChange with a sport code (or 'ALL').
 */
const TABS = [{ code: 'ALL', label: 'All', color: 'var(--navy-500)' }, ...listSports()];

export default function SportFilterTabs({ selected = 'ALL', onChange = () => {} }) {
  return (
    <div
      role="tablist"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8,
        marginBottom: 18,
      }}
    >
      {TABS.map((t) => {
        const active = selected === t.code;
        return (
          <button
            key={t.code}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.code)}
            style={{
              padding: '7px 14px',
              borderRadius: 'var(--radius-full)',
              border: '1px solid ' + (active ? t.color : 'var(--border-default)'),
              background: active ? t.color : 'transparent',
              color: active ? '#fff' : 'var(--fg-secondary)',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              cursor: 'pointer',
              transition: 'all var(--transition)',
            }}
          >
            {t.label || t.code}
          </button>
        );
      })}
    </div>
  );
}
