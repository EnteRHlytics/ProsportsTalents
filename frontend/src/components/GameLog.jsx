import { useEffect, useState } from 'react';
import LoadingSpinner from './ui/LoadingSpinner';
import ErrorMessage from './ui/ErrorMessage';

export default function GameLog({ athleteId }) {
  const [games, setGames] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [season, setSeason] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 5;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load available seasons from stat summary
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/athletes/${athleteId}/stats/summary`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load');
        return res.json();
      })
      .then((data) => {
        const keys = Object.keys(data || {}).filter((s) => s !== 'career').sort();
        setSeasons(keys);
        if (!season && keys.length) {
          setSeason(keys[keys.length - 1]);
        }
      })
      .catch((err) => {
        console.error('Failed to load seasons', err);
        setError('Failed to load seasons');
      })
      .finally(() => setLoading(false));
  }, [athleteId]);

  // Load games when season or page changes
  useEffect(() => {
    if (!athleteId || !season) return;
    const params = new URLSearchParams();
    if (season) params.append('season', season);
    params.append('page', page);
    params.append('per_page', perPage);
    setLoading(true);
    setError(null);
    fetch(`/api/athletes/${athleteId}/game-log?${params.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load');
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setGames(data);
          setTotal(data.length);
        } else {
          setGames(data.items || []);
          setTotal(data.total || 0);
        }
      })
      .catch((err) => {
        console.error('Failed to load game log', err);
        setError('Failed to load game log');
      })
      .finally(() => setLoading(false));
  }, [athleteId, season, page]);

  const lastPage = Math.max(1, Math.ceil(total / perPage));

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="game-log">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Game Log{season ? ` (${season})` : ''}</h3>
        {seasons.length > 0 && (
          <select
            value={season}
            onChange={(e) => {
              setSeason(e.target.value);
              setPage(1);
            }}
            className="bg-surface-700 border border-surface-600 text-slate-300 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent"
          >
            {seasons.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="stat-table w-full text-sm">
          <thead>
            <tr className="bg-surface-700">
              <th className="px-3 py-2 text-left text-slate-400 font-medium">Date</th>
              <th className="px-3 py-2 text-left text-slate-400 font-medium">Opponent</th>
              <th className="px-3 py-2 text-center text-slate-400 font-medium">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-600">
            {games.map((g) => (
              <tr key={g.game_id} className="hover:bg-surface-700 transition-colors">
                <td className="px-3 py-2 text-slate-300">{g.date}</td>
                <td className="px-3 py-2 text-slate-300">{g.opponent_name}</td>
                <td className="px-3 py-2 text-center text-slate-300">
                  {g.home_team_score} - {g.visitor_team_score}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {lastPage > 1 && (
        <div className="flex items-center justify-center gap-3 mt-3">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 text-xs rounded bg-surface-700 text-slate-300 hover:bg-surface-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Prev
          </button>
          <span className="text-xs text-slate-400">{page} / {lastPage}</span>
          <button
            onClick={() => setPage((p) => Math.min(lastPage, p + 1))}
            disabled={page === lastPage}
            className="px-3 py-1 text-xs rounded bg-surface-700 text-slate-300 hover:bg-surface-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
