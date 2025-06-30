import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function AthleteList() {
  const [athletes, setAthletes] = useState([]);
  const [q, setQ] = useState('');
  const [sport, setSport] = useState('');
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
    if (sport) params.append('sport', sport);
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

  return (
    <div className="container">
      <h1>Athletes</h1>
      <div className="filter-controls">
        <input
          type="text"
          placeholder="Search..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="text"
          placeholder="Position"
          value={position}
          onChange={(e) => setPosition(e.target.value)}
        />
        <input
          type="text"
          placeholder="Team"
          value={team}
          onChange={(e) => setTeam(e.target.value)}
        />
        <input
          type="text"
          placeholder="Sport"
          value={sport}
          onChange={(e) => setSport(e.target.value)}
        />
        <input
          type="number"
          placeholder="Min Age"
          value={minAge}
          onChange={(e) => setMinAge(e.target.value)}
        />
        <input
          type="number"
          placeholder="Max Age"
          value={maxAge}
          onChange={(e) => setMaxAge(e.target.value)}
        />
        <button onClick={fetchAthletes}>Search</button>
      </div>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <ul>
          {athletes.map((a) => (
            <li key={a.athlete_id}>
              <Link to={`/athletes/${a.athlete_id}`}>{a.user.full_name}</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
