import React, { useState } from 'react';
import ScoreBreakdown from './ScoreBreakdown';

function MedalBadge({ rank }) {
  const medal =
    rank === 1 ? { bg: '#f1c40f', fg: '#000' } :
    rank === 2 ? { bg: '#bdc3c7', fg: '#000' } :
    rank === 3 ? { bg: '#cd7f32', fg: '#fff' } :
    null;
  if (!medal) {
    return (
      <span
        style={{
          fontFamily: 'var(--font-mono, monospace)',
          color: 'var(--fg-tertiary)',
          minWidth: 28,
          display: 'inline-block',
        }}
      >
        {rank}
      </span>
    );
  }
  return (
    <span
      style={{
        background: medal.bg,
        color: medal.fg,
        borderRadius: '50%',
        width: 26,
        height: 26,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 700,
        fontSize: 12,
      }}
    >
      {rank}
    </span>
  );
}

export default function RankingTable({ rows = [], weights = null }) {
  const [openId, setOpenId] = useState(null);

  if (!rows.length) {
    return (
      <div
        style={{
          padding: 28,
          textAlign: 'center',
          color: 'var(--fg-tertiary)',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          fontSize: 14,
        }}
      >
        No ranked athletes available.
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}
    >
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 13,
          color: 'var(--fg-primary)',
        }}
      >
        <thead>
          <tr style={{ background: 'var(--bg-nav)', textAlign: 'left' }}>
            <th style={{ padding: '10px 12px', width: 60 }}>Rank</th>
            <th style={{ padding: '10px 12px' }}>Athlete</th>
            <th style={{ padding: '10px 12px', width: 80 }}>Sport</th>
            <th style={{ padding: '10px 12px', width: 90, textAlign: 'right' }}>Score</th>
            <th style={{ padding: '10px 12px', width: 90, textAlign: 'right' }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const id = row.athlete_id || row.id || row.name;
            const isOpen = openId === id;
            return (
              <React.Fragment key={id}>
                <tr
                  style={{
                    borderTop: '1px solid var(--border-subtle)',
                  }}
                >
                  <td style={{ padding: '10px 12px' }}>
                    <MedalBadge rank={row.rank} />
                  </td>
                  <td style={{ padding: '10px 12px', fontWeight: 500 }}>
                    {row.name}
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--fg-tertiary)' }}>
                    {row.sport || '—'}
                  </td>
                  <td
                    style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      fontFamily: 'var(--font-mono, monospace)',
                      fontWeight: 600,
                    }}
                  >
                    {Number(row.score).toFixed(1)}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    {row.components && (
                      <button
                        type="button"
                        onClick={() => setOpenId(isOpen ? null : id)}
                        style={{
                          background: 'transparent',
                          border: '1px solid var(--border-default)',
                          color: 'var(--fg-secondary)',
                          padding: '4px 10px',
                          fontSize: 11,
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                        }}
                      >
                        {isOpen ? 'Hide' : 'View'}
                      </button>
                    )}
                  </td>
                </tr>
                {isOpen && row.components && (
                  <tr>
                    <td
                      colSpan={5}
                      style={{
                        padding: 12,
                        background: 'var(--bg-surface-alt, var(--bg-surface))',
                        borderTop: '1px solid var(--border-subtle)',
                      }}
                    >
                      <ScoreBreakdown
                        components={row.components}
                        weights={weights}
                      />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
