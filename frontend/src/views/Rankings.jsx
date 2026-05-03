import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import PageWrapper from '../components/layout/PageWrapper';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import RankingTable from '../components/ranking/RankingTable';
import ExportButtons from '../components/common/ExportButtons';

const SPORTS = [
  { code: 'ALL', label: 'All Sports' },
  { code: 'NBA', label: 'NBA' },
  { code: 'NFL', label: 'NFL' },
  { code: 'MLB', label: 'MLB' },
  { code: 'NHL', label: 'NHL' },
  { code: 'SOC', label: 'Soccer' },
];

const DEFAULT_WEIGHTS = {
  performance: 0.4,
  efficiency: 0.2,
  durability: 0.2,
  fan_perception: 0.1,
  market_value: 0.1,
};

export default function Rankings() {
  const [sport, setSport] = useState('ALL');
  const [limit, setLimit] = useState(10);
  const [rows, setRows] = useState([]);
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [presets, setPresets] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (sport && sport !== 'ALL') params.append('sport', sport);
    params.append('limit', String(limit));
    if (selectedPresetId) params.append('preset_id', selectedPresetId);
    fetch(`/api/rankings/top?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load rankings');
        return res.json();
      })
      .then((data) => {
        setRows(Array.isArray(data) ? data : []);
        // Best-effort fetch of the user's weights for display in the
        // breakdown.  Falls back silently to defaults.
        return fetch('/api/rankings/presets')
          .then((r) => (r.ok ? r.json() : []))
          .then((list) => {
            const arr = Array.isArray(list) ? list : [];
            setPresets(arr);
            const matchingPreset = selectedPresetId
              ? arr.find((p) => String(p.id) === String(selectedPresetId))
              : null;
            const def = matchingPreset || arr.find(
              (p) =>
                p.is_default &&
                (sport === 'ALL'
                  ? p.sport_code == null
                  : p.sport_code === sport),
            );
            if (def && def.weights) setWeights(def.weights);
            else setWeights(DEFAULT_WEIGHTS);
          })
          .catch(() => setWeights(DEFAULT_WEIGHTS));
      })
      .catch(() => setError('Failed to load rankings'))
      .finally(() => setLoading(false));
  }, [sport, limit, selectedPresetId]);

  const exportParams = useMemo(() => {
    const p = {};
    if (sport && sport !== 'ALL') p.sport = sport;
    if (selectedPresetId) p.preset_id = selectedPresetId;
    return p;
  }, [sport, selectedPresetId]);

  const presetOptionsForSport = useMemo(() => {
    return (presets || []).filter((p) =>
      sport === 'ALL' ? p.sport_code == null : p.sport_code === sport || p.sport_code == null,
    );
  }, [presets, sport]);

  return (
    <PageWrapper>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 18,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 38,
              marginBottom: 6,
              fontFamily: 'var(--font-display)',
              color: 'var(--fg-primary)',
            }}
          >
            Top Rankings
          </h1>
          <p
            style={{
              color: 'var(--fg-tertiary)',
              fontSize: 15,
              margin: 0,
            }}
          >
            Multi-factor leaderboard powered by performance, efficiency,
            durability, fan perception and market value scores.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ExportButtons type="rankings" params={exportParams} />
          <Link
            to="/rankings/customize"
            style={{
              padding: '9px 18px',
              background: 'var(--orange-500)',
              color: '#fff',
              fontSize: 13,
              fontWeight: 600,
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontFamily: 'var(--font-body)',
            }}
          >
            Customize Metrics
          </Link>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginBottom: 16,
        }}
      >
        {SPORTS.map((s) => {
          const active = sport === s.code;
          return (
            <button
              key={s.code}
              onClick={() => setSport(s.code)}
              style={{
                padding: '7px 14px',
                fontSize: 13,
                fontWeight: 500,
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                background: active
                  ? 'var(--orange-500)'
                  : 'var(--bg-surface)',
                color: active ? '#fff' : 'var(--fg-secondary)',
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
              }}
            >
              {s.label}
            </button>
          );
        })}
        <div style={{ flex: 1 }} />
        {presetOptionsForSport.length > 0 && (
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              color: 'var(--fg-tertiary)',
              marginRight: 6,
            }}
          >
            Preset
            <select
              value={selectedPresetId}
              onChange={(e) => setSelectedPresetId(e.target.value)}
              style={{
                padding: '6px 8px',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--fg-primary)',
                fontSize: 12,
              }}
            >
              <option value="">Default</option>
              {presetOptionsForSport.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
        )}
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            color: 'var(--fg-tertiary)',
          }}
        >
          Show
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{
              padding: '6px 8px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--fg-primary)',
              fontSize: 12,
            }}
          >
            <option value={10}>Top 10</option>
            <option value={25}>Top 25</option>
            <option value={50}>Top 50</option>
            <option value={100}>Top 100</option>
          </select>
        </label>
      </div>

      <ErrorMessage message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <RankingTable rows={rows} weights={weights} />
      )}
    </PageWrapper>
  );
}
