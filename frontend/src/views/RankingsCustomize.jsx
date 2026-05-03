import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import PageWrapper from '../components/layout/PageWrapper';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import WeightSlider from '../components/ranking/WeightSlider';
import RankingTable from '../components/ranking/RankingTable';

const SPORTS = [
  { code: '', label: 'All Sports' },
  { code: 'NBA', label: 'NBA' },
  { code: 'NFL', label: 'NFL' },
  { code: 'MLB', label: 'MLB' },
  { code: 'NHL', label: 'NHL' },
  { code: 'SOC', label: 'Soccer' },
];

const COMPONENT_KEYS = [
  'performance',
  'efficiency',
  'durability',
  'fan_perception',
  'market_value',
];

const DEFAULT_WEIGHTS = {
  performance: 0.4,
  efficiency: 0.2,
  durability: 0.2,
  fan_perception: 0.1,
  market_value: 0.1,
};

function normalise(weights) {
  const total = COMPONENT_KEYS.reduce(
    (acc, k) => acc + Math.max(0, Number(weights[k]) || 0),
    0,
  );
  if (total <= 0) return { ...DEFAULT_WEIGHTS };
  const out = {};
  COMPONENT_KEYS.forEach((k) => {
    out[k] = Math.max(0, Number(weights[k]) || 0) / total;
  });
  return out;
}

export default function RankingsCustomize() {
  const [sport, setSport] = useState('');
  const [name, setName] = useState('My Preset');
  const [isDefault, setIsDefault] = useState(false);
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [preview, setPreview] = useState([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [savedMessage, setSavedMessage] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const normalised = useMemo(() => normalise(weights), [weights]);

  // Load presets on mount.
  useEffect(() => {
    fetch('/api/rankings/presets')
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setPresets(Array.isArray(data) ? data : []))
      .catch(() => setPresets([]));
  }, []);

  // Live preview whenever weights / sport change.
  useEffect(() => {
    setLoadingPreview(true);
    setPreviewError(null);
    fetch('/api/rankings/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sport: sport || undefined,
        weights: normalised,
        limit: 10,
      }),
    })
      .then((r) => {
        if (!r.ok) throw new Error('preview failed');
        return r.json();
      })
      .then((data) => setPreview(data?.results || []))
      .catch(() => setPreviewError('Failed to compute preview'))
      .finally(() => setLoadingPreview(false));
  }, [sport, normalised.performance, normalised.efficiency, normalised.durability, normalised.fan_perception, normalised.market_value]);

  function updateWeight(key, value) {
    setWeights((prev) => ({ ...prev, [key]: value }));
  }

  function loadPreset(id) {
    setSelectedPreset(id);
    if (!id) {
      setWeights(DEFAULT_WEIGHTS);
      setName('My Preset');
      setIsDefault(false);
      setSport('');
      return;
    }
    const preset = presets.find((p) => p.id === id);
    if (!preset) return;
    setWeights({ ...DEFAULT_WEIGHTS, ...preset.weights });
    setName(preset.name || 'My Preset');
    setIsDefault(Boolean(preset.is_default));
    setSport(preset.sport_code || '');
  }

  function resetToDefaults() {
    setWeights(DEFAULT_WEIGHTS);
  }

  function savePreset() {
    setSavedMessage(null);
    setSaveError(null);
    fetch('/api/rankings/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        sport: sport || undefined,
        weights: normalised,
        is_default: isDefault,
      }),
    })
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(body.error || 'Failed to save');
        return body;
      })
      .then((preset) => {
        setSavedMessage(`Saved preset "${preset.name}".`);
        setPresets((prev) => {
          const others = prev.filter((p) => p.id !== preset.id);
          return [preset, ...others];
        });
        setSelectedPreset(preset.id);
      })
      .catch((err) => setSaveError(err.message || 'Failed to save'));
  }

  return (
    <PageWrapper>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          marginBottom: 18,
          flexWrap: 'wrap',
          gap: 10,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 34,
              marginBottom: 6,
              fontFamily: 'var(--font-display)',
              color: 'var(--fg-primary)',
            }}
          >
            Customize Ranking Weights
          </h1>
          <p
            style={{
              color: 'var(--fg-tertiary)',
              fontSize: 14,
              margin: 0,
            }}
          >
            Adjust how much each component contributes to the overall score.
            Weights are auto-normalised to sum to 100%.
          </p>
        </div>
        <Link
          to="/rankings"
          style={{
            padding: '9px 18px',
            background: 'transparent',
            color: 'var(--fg-secondary)',
            border: '1px solid var(--border-default)',
            fontSize: 13,
            borderRadius: 'var(--radius-md)',
            textDecoration: 'none',
          }}
        >
          Back to Rankings
        </Link>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 360px) minmax(0, 1fr)',
          gap: 24,
          alignItems: 'flex-start',
        }}
      >
        {/* Sliders & save */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: 18,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>
              Load preset
              <select
                value={selectedPreset}
                onChange={(e) => loadPreset(e.target.value)}
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: 4,
                  padding: '6px 8px',
                  background: 'var(--bg-page)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--fg-primary)',
                  fontSize: 13,
                }}
              >
                <option value="">— Defaults —</option>
                {presets.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {p.sport_code ? ` (${p.sport_code})` : ''}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>
              Sport scope
              <select
                value={sport}
                onChange={(e) => setSport(e.target.value)}
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: 4,
                  padding: '6px 8px',
                  background: 'var(--bg-page)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--fg-primary)',
                  fontSize: 13,
                }}
              >
                {SPORTS.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {COMPONENT_KEYS.map((key) => (
            <WeightSlider
              key={key}
              componentKey={key}
              value={weights[key] ?? 0}
              onChange={updateWeight}
            />
          ))}

          <div
            style={{
              fontSize: 11,
              color: 'var(--fg-tertiary)',
              marginBottom: 16,
              textAlign: 'right',
              fontFamily: 'var(--font-mono, monospace)',
            }}
          >
            Auto-normalised total: 100%
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              borderTop: '1px solid var(--border-subtle)',
              paddingTop: 14,
            }}
          >
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Preset name"
              style={{
                padding: '8px 10px',
                background: 'var(--bg-page)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--fg-primary)',
                fontSize: 13,
              }}
            />
            <label
              style={{
                fontSize: 12,
                color: 'var(--fg-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <input
                type="checkbox"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
              />
              Set as default for {sport ? sport : 'all sports'}
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                onClick={savePreset}
                style={{
                  flex: 1,
                  padding: '9px 14px',
                  background: 'var(--orange-500)',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                }}
              >
                Save Preset
              </button>
              <button
                type="button"
                onClick={resetToDefaults}
                style={{
                  padding: '9px 14px',
                  background: 'transparent',
                  color: 'var(--fg-secondary)',
                  border: '1px solid var(--border-default)',
                  fontSize: 13,
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                }}
              >
                Reset
              </button>
            </div>
            {savedMessage && (
              <div style={{ color: 'var(--green-500, #2ea65c)', fontSize: 12 }}>
                {savedMessage}
              </div>
            )}
            {saveError && (
              <div style={{ color: '#e57373', fontSize: 12 }}>{saveError}</div>
            )}
          </div>
        </div>

        {/* Live preview */}
        <div>
          <div
            style={{
              fontSize: 13,
              color: 'var(--fg-tertiary)',
              marginBottom: 8,
              textTransform: 'uppercase',
              letterSpacing: 0.6,
            }}
          >
            Live preview — top 10
          </div>
          <ErrorMessage message={previewError} />
          {loadingPreview ? (
            <LoadingSpinner />
          ) : (
            <RankingTable rows={preview} weights={normalised} />
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
