import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

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

  const inputCls = 'px-2 py-1 bg-surface-700 border border-surface-600 rounded text-sm text-slate-100 focus:outline-none focus:border-accent';

  return (
    <div>
      <h3 className="text-sm font-semibold text-white mb-3">Stats</h3>
      <ul className="stat-list space-y-1.5 mb-3">
        {stats.map((s) => (
          <li key={s.stat_id} className="flex items-center justify-between gap-2">
            <span className="text-slate-300 text-xs truncate">
              <span className="font-medium">{s.name}</span>
              {s.season && <span className="text-slate-500"> ({s.season})</span>}
              <span className="text-slate-400 ml-1">: {s.value}</span>
            </span>
            <button
              onClick={() => deleteStat(s.stat_id)}
              className="text-slate-500 hover:text-red-400 transition-colors flex-shrink-0"
            >
              <X size={14} />
            </button>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <input
          placeholder="Stat name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`${inputCls} flex-1 min-w-[100px]`}
        />
        <input
          placeholder="Value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className={`${inputCls} w-20`}
        />
        <input
          placeholder="Season"
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          className={`${inputCls} w-20`}
        />
        <button
          type="button"
          onClick={addStat}
          className="px-3 py-1 bg-accent hover:bg-indigo-500 text-white text-xs font-medium rounded transition-colors"
        >
          Add
        </button>
      </div>
    </div>
  );
}
