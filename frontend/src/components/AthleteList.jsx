import { useEffect, useState } from 'react';
import PageWrapper from './layout/PageWrapper';
import AthleteGrid from './athlete/AthleteGrid';
import SportFilterTabs from './athlete/SportFilterTabs';
import SearchBar from './athlete/SearchBar';
import LoadingSpinner from './ui/LoadingSpinner';
import ErrorMessage from './ui/ErrorMessage';

const inputStyle = {
  padding: '9px 12px',
  background: 'var(--bg-surface)',
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  color: 'var(--fg-primary)',
  outline: 'none',
  fontFamily: 'var(--font-body)',
  transition: 'border-color var(--transition)',
};

export default function AthleteList() {
  const [athletes, setAthletes] = useState([]);
  const [q, setQ] = useState('');
  const [sport, setSport] = useState('ALL');
  const [position, setPosition] = useState('');
  const [team, setTeam] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAthletes = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (sport && sport !== 'ALL') params.append('sport', sport);
    if (position) params.append('position', position);
    if (team) params.append('team', team);
    if (minAge) params.append('min_age', minAge);
    if (maxAge) params.append('max_age', maxAge);
    if (name) params.append('name', name);
    fetch(`/api/athletes/search?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then((data) => setAthletes(data.results || []))
      .catch(() => setError('Failed to fetch athletes'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAthletes(); }, []);
  useEffect(() => { fetchAthletes(); }, [sport]);

  return (
    <PageWrapper>
      <h1 style={{ fontSize: 38, marginBottom: 6, fontFamily: 'var(--font-display)', color: 'var(--fg-primary)' }}>
        Discover Athletes
      </h1>
      <p style={{ color: 'var(--fg-tertiary)', marginBottom: 28, fontSize: 15 }}>
        Browse professional athletes across 5 sports leagues.
      </p>

      <SportFilterTabs selected={sport} onChange={setSport} />

      {/* Search & filters */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 24, alignItems: 'center' }}>
        <div style={{ flex: '1 1 240px', minWidth: 200 }}>
          <SearchBar value={q} onChange={setQ} placeholder="Search all athletes..." />
        </div>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={inputStyle}
          onFocus={e => e.target.style.borderColor = 'var(--navy-500)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
        />
        <input
          type="text"
          placeholder="Position"
          value={position}
          onChange={(e) => setPosition(e.target.value)}
          style={{ ...inputStyle, width: 110 }}
          onFocus={e => e.target.style.borderColor = 'var(--navy-500)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
        />
        <input
          type="text"
          placeholder="Team"
          value={team}
          onChange={(e) => setTeam(e.target.value)}
          style={{ ...inputStyle, width: 110 }}
          onFocus={e => e.target.style.borderColor = 'var(--navy-500)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
        />
        <input
          type="number"
          placeholder="Min Age"
          value={minAge}
          onChange={(e) => setMinAge(e.target.value)}
          style={{ ...inputStyle, width: 90 }}
          onFocus={e => e.target.style.borderColor = 'var(--navy-500)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
        />
        <input
          type="number"
          placeholder="Max Age"
          value={maxAge}
          onChange={(e) => setMaxAge(e.target.value)}
          style={{ ...inputStyle, width: 90 }}
          onFocus={e => e.target.style.borderColor = 'var(--navy-500)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
        />
        <button
          onClick={fetchAthletes}
          style={{
            padding: '9px 18px',
            background: 'var(--orange-500)',
            color: '#fff',
            fontSize: 13,
            fontWeight: 600,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'var(--font-body)',
            transition: 'opacity var(--transition)',
          }}
          onMouseEnter={e => e.currentTarget.style.opacity = '0.88'}
          onMouseLeave={e => e.currentTarget.style.opacity = '1'}
        >
          Search
        </button>
      </div>

      {athletes.length > 0 && (
        <div style={{ fontSize: 13, color: 'var(--fg-tertiary)', marginBottom: 16 }}>
          {athletes.length} athlete{athletes.length !== 1 ? 's' : ''} found
        </div>
      )}

      <ErrorMessage message={error} />
      {loading ? <LoadingSpinner /> : <AthleteGrid athletes={athletes} />}
    </PageWrapper>
  );
}
