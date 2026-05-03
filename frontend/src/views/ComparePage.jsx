import { useEffect, useMemo, useState } from 'react';
import { Search, X, Plus, Users } from 'lucide-react';
import PageWrapper from '../components/layout/PageWrapper';
import EmptyState from '../components/common/EmptyState';
import ErrorBanner from '../components/common/ErrorBanner';
import { MultiSkillRadar } from '../components/charts/SkillRadar';
import { getSportConfig } from '../utils/sportConfig';
import { apiFetch } from '../hooks/useApi';

const COMPARE_COLORS = ['var(--orange-500)', 'var(--steel-500)', 'var(--green-500)', 'var(--orange-300)'];
const MAX_SELECTED = 4;
const MIN_SELECTED = 2;

function fullName(a) {
  return a?.user?.full_name
    || `${a?.user?.first_name || a?.first_name || ''} ${a?.user?.last_name || a?.last_name || ''}`.trim()
    || a?.name
    || 'Athlete';
}

function getId(a) {
  return a?.athlete_id ?? a?.id;
}

export default function ComparePage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [selected, setSelected] = useState([]); // array of full athlete objects
  const [details, setDetails] = useState({}); // id -> { athlete, skills, summary }
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Debounced search
  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setResults([]);
      return;
    }
    let cancelled = false;
    setSearching(true);
    setSearchError(null);
    const t = setTimeout(async () => {
      try {
        const data = await apiFetch(`/athletes/search?q=${encodeURIComponent(query.trim())}&per_page=8`);
        if (cancelled) return;
        setResults(data?.results || (Array.isArray(data) ? data : []));
      } catch (e) {
        if (!cancelled) setSearchError(e);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 250);
    return () => { cancelled = true; clearTimeout(t); };
  }, [query]);

  // Load details (skills + season summary) when selection changes
  useEffect(() => {
    let cancelled = false;
    async function loadAll() {
      const ids = selected.map(getId).filter(Boolean);
      if (!ids.length) { setDetails({}); return; }
      setLoadingDetails(true);
      const out = { ...details };
      await Promise.all(ids.map(async (id) => {
        if (out[id]) return; // already cached
        try {
          const [skills, summary] = await Promise.all([
            apiFetch(`/athletes/${id}/skills`).catch(() => []),
            apiFetch(`/athletes/${id}/stats/summary`).catch(() => ({})),
          ]);
          out[id] = {
            skills: Array.isArray(skills) ? skills : [],
            summary: summary && typeof summary === 'object' ? summary : {},
          };
        } catch {
          out[id] = { skills: [], summary: {} };
        }
      }));
      if (!cancelled) {
        // prune cache to selected only
        const pruned = {};
        ids.forEach((id) => { if (out[id]) pruned[id] = out[id]; });
        setDetails(pruned);
        setLoadingDetails(false);
      }
    }
    loadAll();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected.map(getId).join('|')]);

  const addAthlete = (a) => {
    if (selected.length >= MAX_SELECTED) return;
    if (selected.some((s) => getId(s) === getId(a))) return;
    setSelected([...selected, a]);
    setQuery('');
    setResults([]);
  };

  const removeAthlete = (id) => {
    setSelected((cur) => cur.filter((a) => getId(a) !== id));
  };

  // Build the merged stat columns from latest season of each athlete
  const statsTable = useMemo(() => {
    if (!selected.length) return { columns: [], rows: [] };
    const perAthlete = selected.map((a) => {
      const id = getId(a);
      const summary = details[id]?.summary || {};
      // pick latest season key (skip "career" if present)
      const seasonKeys = Object.keys(summary).filter((k) => k.toLowerCase() !== 'career').sort();
      const latest = seasonKeys[seasonKeys.length - 1];
      const stats = (latest ? summary[latest] : null) || summary.career || {};
      return { athlete: a, season: latest || 'career', stats };
    });
    const allStatNames = Array.from(new Set(perAthlete.flatMap((p) => Object.keys(p.stats || {}))));
    return {
      columns: perAthlete,
      rows: allStatNames.map((name) => ({
        name,
        values: perAthlete.map((p) => p.stats?.[name]),
      })),
    };
  }, [selected, details]);

  // Build series for radar
  const radarSeries = selected.map((a, i) => ({
    label: fullName(a),
    color: COMPARE_COLORS[i % COMPARE_COLORS.length],
    skills: details[getId(a)]?.skills || [],
  }));

  return (
    <PageWrapper>
      <div style={{ marginBottom: 18 }}>
        <span style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--orange-500)' }}>
          Analytics
        </span>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(28px, 4vw, 38px)', margin: '4px 0 6px', color: 'var(--fg-primary)' }}>
          Compare Athletes
        </h1>
        <p style={{ color: 'var(--fg-tertiary)', fontSize: 14, margin: 0 }}>
          Pick {MIN_SELECTED}–{MAX_SELECTED} athletes to see their stats and skills side-by-side.
        </p>
      </div>

      {/* Search & selection chips */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: 14,
          marginBottom: 20,
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', marginBottom: 10 }}>
          {selected.map((a, i) => {
            const id = getId(a);
            return (
              <span
                key={id}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 10px',
                  background: COMPARE_COLORS[i % COMPARE_COLORS.length],
                  color: '#fff',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {fullName(a)}
                <button
                  type="button"
                  aria-label={`Remove ${fullName(a)}`}
                  onClick={() => removeAthlete(id)}
                  style={{
                    background: 'rgba(0,0,0,0.25)',
                    border: 'none',
                    color: '#fff',
                    width: 18,
                    height: 18,
                    borderRadius: '50%',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <X size={12} />
                </button>
              </span>
            );
          })}
          {selected.length < MAX_SELECTED && (
            <span style={{ fontSize: 12, color: 'var(--fg-tertiary)' }}>
              {selected.length === 0 ? 'No athletes selected' : `${selected.length} selected · add up to ${MAX_SELECTED}`}
            </span>
          )}
        </div>

        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--fg-tertiary)' }} />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={selected.length >= MAX_SELECTED ? 'Selection limit reached' : 'Search athletes by name…'}
            disabled={selected.length >= MAX_SELECTED}
            style={{
              width: '100%',
              padding: '10px 12px 10px 34px',
              background: 'var(--bg-surface-alt)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              fontSize: 14,
              color: 'var(--fg-primary)',
              outline: 'none',
            }}
          />
        </div>

        {searchError && (
          <div style={{ marginTop: 10 }}>
            <ErrorBanner message="Couldn't reach the athletes service." compact />
          </div>
        )}

        {!!query && results.length === 0 && !searching && !searchError && (
          <div style={{ marginTop: 10, fontSize: 13, color: 'var(--fg-tertiary)' }}>No matches.</div>
        )}

        {results.length > 0 && (
          <ul
            style={{
              listStyle: 'none',
              margin: '10px 0 0',
              padding: 0,
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-alt)',
              overflow: 'hidden',
            }}
          >
            {results.map((a) => {
              const cfg = getSportConfig(a.primary_sport?.code);
              const alreadyPicked = selected.some((s) => getId(s) === getId(a));
              return (
                <li
                  key={getId(a)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '8px 12px',
                    borderBottom: '1px solid var(--border-subtle)',
                    fontSize: 13,
                    color: 'var(--fg-secondary)',
                  }}
                >
                  <span style={{ flex: 1, minWidth: 0, color: 'var(--fg-primary)' }}>{fullName(a)}</span>
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
                  <button
                    type="button"
                    onClick={() => addAthlete(a)}
                    disabled={alreadyPicked || selected.length >= MAX_SELECTED}
                    style={{
                      background: alreadyPicked ? 'var(--bg-surface)' : 'var(--orange-500)',
                      color: alreadyPicked ? 'var(--fg-tertiary)' : '#fff',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      padding: '4px 10px',
                      fontSize: 12,
                      cursor: alreadyPicked ? 'default' : 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    <Plus size={12} /> {alreadyPicked ? 'Added' : 'Add'}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Comparison body */}
      {selected.length < MIN_SELECTED ? (
        <EmptyState
          icon={Users}
          title="Select at least 2 athletes"
          description="Use the search above to pick athletes to compare."
        />
      ) : (
        <>
          {/* Stats table */}
          <section
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: 16,
              marginBottom: 20,
              overflowX: 'auto',
            }}
          >
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, margin: '0 0 12px', color: 'var(--fg-primary)' }}>
              Latest-Season Stats
            </h2>
            {loadingDetails ? (
              <div style={{ color: 'var(--fg-tertiary)', fontSize: 13, padding: 8 }}>Loading stats…</div>
            ) : statsTable.rows.length === 0 ? (
              <EmptyState compact title="No stats available" description="The selected athletes don't have season stats yet." />
            ) : (
              <table className="stat-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Stat</th>
                    {statsTable.columns.map((c, i) => (
                      <th key={getId(c.athlete)} style={{ color: COMPARE_COLORS[i % COMPARE_COLORS.length] }}>
                        {fullName(c.athlete)}
                        <div style={{ fontSize: 10, fontWeight: 400, color: 'var(--fg-tertiary)', textTransform: 'none', letterSpacing: 0 }}>
                          {c.season}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {statsTable.rows.map((row) => {
                    // find max numeric value for highlighting
                    const nums = row.values.map((v) => parseFloat(v));
                    const max = Math.max(...nums.filter((n) => !isNaN(n)));
                    return (
                      <tr key={row.name}>
                        <td style={{ textAlign: 'left', color: 'var(--fg-secondary)', fontWeight: 500 }}>{row.name}</td>
                        {row.values.map((v, j) => {
                          const n = parseFloat(v);
                          const isMax = !isNaN(n) && nums.filter((x) => !isNaN(x)).length > 1 && n === max;
                          return (
                            <td
                              key={j}
                              style={{
                                fontWeight: isMax ? 700 : 500,
                                color: isMax ? 'var(--orange-500)' : 'var(--fg-secondary)',
                                background: isMax ? 'var(--orange-100)' : 'transparent',
                              }}
                            >
                              {v ?? '—'}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </section>

          {/* Radar */}
          <section
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: 16,
            }}
          >
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, margin: '0 0 12px', color: 'var(--fg-primary)' }}>
              Skill Comparison
            </h2>
            <MultiSkillRadar series={radarSeries} />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 8 }}>
              {radarSeries.map((s) => (
                <span key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--fg-secondary)' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: s.color }} />
                  {s.label}
                </span>
              ))}
            </div>
          </section>
        </>
      )}
    </PageWrapper>
  );
}
