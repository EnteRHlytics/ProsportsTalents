import React from 'react';

const COMPONENT_LABELS = {
  performance: 'Performance',
  efficiency: 'Efficiency',
  durability: 'Durability',
  fan_perception: 'Fan Perception',
  market_value: 'Market Value',
};

const COMPONENT_HINTS = {
  performance: 'Core production stats (e.g. PPG, passing yards).',
  efficiency: 'Advanced ratios (TS%, OPS, passer rating, +/-).',
  durability: 'Games played versus full season length.',
  fan_perception: 'Featured / verified status (placeholder).',
  market_value: 'Experience curve and overall rating (placeholder).',
};

export default function WeightSlider({
  componentKey,
  value,
  onChange,
  disabled = false,
}) {
  const label = COMPONENT_LABELS[componentKey] || componentKey;
  const hint = COMPONENT_HINTS[componentKey] || '';
  const pct = Math.round((Number(value) || 0) * 100);

  return (
    <div style={{ marginBottom: 18 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 4,
        }}
      >
        <label
          htmlFor={`weight-${componentKey}`}
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--fg-primary)',
            fontFamily: 'var(--font-body)',
          }}
        >
          {label}
        </label>
        <span
          style={{
            fontSize: 12,
            fontFamily: 'var(--font-mono, monospace)',
            color: 'var(--fg-secondary)',
            minWidth: 38,
            textAlign: 'right',
          }}
        >
          {pct}%
        </span>
      </div>
      <input
        id={`weight-${componentKey}`}
        type="range"
        min={0}
        max={100}
        step={1}
        value={pct}
        disabled={disabled}
        onChange={(e) => onChange(componentKey, Number(e.target.value) / 100)}
        style={{
          width: '100%',
          accentColor: 'var(--orange-500)',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      />
      <div
        style={{
          fontSize: 11,
          color: 'var(--fg-tertiary)',
          marginTop: 2,
        }}
      >
        {hint}
      </div>
    </div>
  );
}
