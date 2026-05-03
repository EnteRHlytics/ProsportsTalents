import React from 'react';

const COMPONENT_LABELS = {
  performance: 'Performance',
  efficiency: 'Efficiency',
  durability: 'Durability',
  fan_perception: 'Fan Perception',
  market_value: 'Market Value',
};

function Bar({ value }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div
      style={{
        flex: 1,
        height: 6,
        background: 'var(--bg-surface-alt, rgba(255,255,255,0.05))',
        borderRadius: 3,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: '100%',
          background: 'var(--orange-500)',
          transition: 'width 200ms ease',
        }}
      />
    </div>
  );
}

export default function ScoreBreakdown({ components, weights }) {
  if (!components) return null;
  const keys = Object.keys(components);
  return (
    <div
      style={{
        background: 'var(--bg-surface-alt, var(--bg-surface))',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 12,
        minWidth: 280,
      }}
    >
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--fg-secondary)',
          textTransform: 'uppercase',
          letterSpacing: 0.6,
          marginBottom: 10,
        }}
      >
        Score Breakdown
      </div>
      {keys.map((key) => {
        const val = components[key];
        const weight = weights ? weights[key] : null;
        return (
          <div
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 110,
                fontSize: 12,
                color: 'var(--fg-primary)',
              }}
            >
              {COMPONENT_LABELS[key] || key}
            </div>
            <Bar value={val} />
            <div
              style={{
                width: 56,
                textAlign: 'right',
                fontSize: 12,
                fontFamily: 'var(--font-mono, monospace)',
                color: 'var(--fg-secondary)',
              }}
            >
              {Number(val).toFixed(1)}
              {weight != null && (
                <span style={{ color: 'var(--fg-tertiary)', marginLeft: 4 }}>
                  &times;{(weight * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
