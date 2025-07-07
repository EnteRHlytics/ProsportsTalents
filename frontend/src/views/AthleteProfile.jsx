import { useParams, Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import SkillEditor from '../components/SkillEditor';
import StatEditor from '../components/StatEditor';
import StatChart from '../components/StatChart';
import SeasonStats from '../components/SeasonStats';
import GameLog from '../components/GameLog';

export default function AthleteProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [athlete, setAthlete] = useState(null);
  const [statsTab, setStatsTab] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/athletes/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load');
        return res.json();
      })
      .then((data) => setAthlete(data))
      .catch((err) => {
        console.error('Failed to fetch athlete', err);
        setError('Failed to load athlete');
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = () => {
    if (!window.confirm('Delete this athlete?')) return;
    fetch(`/api/athletes/${id}`, { method: 'DELETE' })
      .then((res) => {
        if (res.ok) navigate('/');
      })
      .catch((err) => console.error('Failed to delete athlete', err));
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!athlete) {
    return <div>Loading...</div>;
  }

  return (
    <div className="profile-container container">
      <div className="container">

      <h2>{athlete.user.full_name}</h2>
      <p>{athlete.bio}</p>
      <p>Date of Birth: {athlete.date_of_birth}</p>
      <div className="form-row">
        <Link to={`/athletes/${id}/edit`}>Edit</Link>
        <button onClick={handleDelete} style={{ marginLeft: '1rem' }}>
          Delete
        </button>
      </div>
      <SkillEditor athleteId={id} />
      <StatEditor athleteId={id} />

      <div className="stats-section">
        <h3>Stats</h3>
        <div className="tabs">
          <button
            className={`tab-button ${statsTab === 'summary' ? 'active' : ''}`}
            onClick={() => setStatsTab('summary')}
          >
            Overview
          </button>
          <button
            className={`tab-button ${statsTab === 'gameLog' ? 'active' : ''}`}
            onClick={() => setStatsTab('gameLog')}
          >
            Game Log
          </button>
          <button
            className={`tab-button ${statsTab === 'chart' ? 'active' : ''}`}
            onClick={() => setStatsTab('chart')}
          >
            Charts
          </button>
        </div>
        {statsTab === 'summary' && <SeasonStats athleteId={id} />}
        {statsTab === 'gameLog' && <GameLog athleteId={id} />}
        {statsTab === 'chart' && <StatChart athleteId={id} />}
      </div>
    </div>
    </div>
  );
}
