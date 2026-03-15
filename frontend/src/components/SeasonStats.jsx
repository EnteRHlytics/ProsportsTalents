import { useEffect, useState } from 'react';
import { computeSeasonData } from '../utils/stats.js';
import LoadingSpinner from './ui/LoadingSpinner';
import ErrorMessage from './ui/ErrorMessage';

export default function SeasonStats({ athleteId }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
        setSummary(data);
      })
      .catch((err) => {
        console.error('Failed to load stat summary', err);
        setError('Failed to load stats');
      })
      .finally(() => setLoading(false));
  }, [athleteId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!summary) return null;

  const { seasons, columns, highs } = computeSeasonData(summary);

  return (
    <div className="season-stats">
      <h3 className="text-sm font-semibold text-white mb-3">Season Totals</h3>
      <div className="overflow-x-auto">
        <table className="stat-table w-full text-sm">
          <thead>
            <tr className="bg-surface-700">
              <th className="px-3 py-2 text-left text-slate-400 font-medium">Season</th>
              {columns.map((name) => (
                <th key={name} className="px-3 py-2 text-center text-slate-400 font-medium">{name}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-600">
            {seasons.map((season) => (
              <tr key={season} className="hover:bg-surface-700 transition-colors">
                <td className="px-3 py-2 text-slate-300 font-medium">{season}</td>
                {columns.map((name) => {
                  const value = summary[season][name];
                  const num = parseFloat(value);
                  const isHigh = !isNaN(num) && num === highs[name];
                  return (
                    <td
                      key={name}
                      className={`px-3 py-2 text-center ${isHigh ? 'career-high text-rating-elite font-bold' : 'text-slate-300'}`}
                    >
                      {value || '—'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
