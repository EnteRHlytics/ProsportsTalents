import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

export default function StatChart({ athleteId }) {
  const [summary, setSummary] = useState(null);
  const [statNames, setStatNames] = useState([]);
  const [selected, setSelected] = useState('');
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
        const names = new Set();
        Object.values(data).forEach((stats) => {
          Object.keys(stats).forEach((n) => names.add(n));
        });
        const arr = Array.from(names);
        setStatNames(arr);
        if (arr.length) setSelected(arr[0]);
      })
      .catch((err) => {
        console.error('Failed to load stat summary', err);
        setError('Failed to load stats');
      })
      .finally(() => setLoading(false));
  }, [athleteId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!summary || !selected) return null;

  const seasons = Object.keys(summary).sort();
  const values = seasons.map((s) => Number(summary[s][selected]) || 0);

  const data = {
    labels: seasons,
    datasets: [
      {
        label: selected,
        data: values,
        borderColor: '#007bff',
        backgroundColor: 'rgba(0,123,255,0.5)',
      },
    ],
  };

  return (
    <div className="stat-chart">
      <h3>{selected} by Season</h3>
      {statNames.length > 1 && (
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {statNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      )}
      <Line data={data} />
    </div>
  );
}
