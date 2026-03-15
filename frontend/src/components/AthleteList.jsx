import { useEffect, useState } from 'react';
import PageWrapper from './layout/PageWrapper';
import AthleteGrid from './athlete/AthleteGrid';
import SportFilterTabs from './athlete/SportFilterTabs';
import SearchBar from './athlete/SearchBar';
import LoadingSpinner from './ui/LoadingSpinner';
import ErrorMessage from './ui/ErrorMessage';

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
      .catch((err) => {
        console.error('Failed to fetch athletes', err);
        setError('Failed to fetch athletes');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAthletes();
  }, []);

  // Re-fetch when sport filter changes
  useEffect(() => {
    fetchAthletes();
  }, [sport]);

  return (
    <PageWrapper>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-white">Discover Athletes</h1>
      </div>

      <SportFilterTabs selected={sport} onChange={setSport} />

      {/* Search & filters row */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex-1 min-w-[200px]">
          <SearchBar value={q} onChange={setQ} placeholder="Search all athletes..." />
        </div>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent"
        />
        <input
          type="text"
          placeholder="Position"
          value={position}
          onChange={(e) => setPosition(e.target.value)}
          className="px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent w-28"
        />
        <input
          type="text"
          placeholder="Team"
          value={team}
          onChange={(e) => setTeam(e.target.value)}
          className="px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent w-28"
        />
        <input
          type="number"
          placeholder="Min Age"
          value={minAge}
          onChange={(e) => setMinAge(e.target.value)}
          className="px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent w-24"
        />
        <input
          type="number"
          placeholder="Max Age"
          value={maxAge}
          onChange={(e) => setMaxAge(e.target.value)}
          className="px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent w-24"
        />
        <button
          onClick={fetchAthletes}
          className="px-4 py-2 bg-accent hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Search
        </button>
      </div>

      <ErrorMessage message={error} />
      {loading ? <LoadingSpinner /> : <AthleteGrid athletes={athletes} />}
    </PageWrapper>
  );
}
