import { useEffect, useState } from 'react';

export default function StatEditor({ athleteId }) {
  const [stats, setStats] = useState([]);
  const [name, setName] = useState('');
  const [value, setValue] = useState('');
  const [season, setSeason] = useState('');

  const load = () => {
    fetch(`/api/athletes/${athleteId}/stats`)
      .then((res) => res.json())
      .then(setStats)
      .catch((err) => console.error('Failed to load stats', err));
  };

  useEffect(() => {
    if (athleteId) load();
  }, [athleteId]);

  const addStat = () => {
    fetch(`/api/athletes/${athleteId}/stats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, value, season }),
    })
      .then((res) => res.json())
      .then((s) => {
        setStats([...stats, s]);
        setName('');
        setValue('');
        setSeason('');
      })
      .catch((err) => console.error('Failed to add stat', err));
  };

  const deleteStat = (statId) => {
    fetch(`/api/stats/${statId}`, { method: 'DELETE' })
      .then(() => setStats(stats.filter((s) => s.stat_id !== statId)))
      .catch((err) => console.error('Failed to delete stat', err));
  };

  return (
    <div>
      <h3>Stats</h3>
      <ul className="stat-list">
        {stats.map((s) => (
          <li key={s.stat_id}>
            <span>
              {s.name} {s.season && `(${s.season})`} : {s.value}
            </span>
            <button onClick={() => deleteStat(s.stat_id)}>x</button>
          </li>
        ))}
      </ul>
      <div className="form-row">
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          placeholder="Value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        <input
          placeholder="Season"
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          style={{ width: '80px' }}
        />
        <button type="button" onClick={addStat}>
          Add
        </button>
      </div>
    </div>
  );
}
