import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import SkillEditor from '../components/SkillEditor';
import StatEditor from '../components/StatEditor';
import StatChart from '../components/StatChart';
import SeasonStats from '../components/SeasonStats';
import GameLog from '../components/GameLog';
import ProfileHero from '../components/athlete/ProfileHero';
import MediaGallery from '../components/athlete/MediaGallery';
import SkillRadar from '../components/charts/SkillRadar';
import PageWrapper from '../components/layout/PageWrapper';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { getSportConfig } from '../utils/sportConfig';

export default function AthleteProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [athlete, setAthlete] = useState(null);
  const [skills, setSkills] = useState([]);
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

  // Load skills for radar tab
  useEffect(() => {
    if (!id) return;
    fetch(`/api/athletes/${id}/skills`)
      .then((r) => r.json())
      .then((d) => setSkills(Array.isArray(d) ? d : []))
      .catch(() => setSkills([]));
  }, [id]);

  const handleDelete = () => {
    if (!window.confirm('Delete this athlete?')) return;
    fetch(`/api/athletes/${id}`, { method: 'DELETE' })
      .then((res) => {
        if (res.ok) navigate('/discover');
      })
      .catch((err) => console.error('Failed to delete athlete', err));
  };

  if (loading) return <PageWrapper><LoadingSpinner /></PageWrapper>;
  if (error) return <PageWrapper><ErrorMessage message={error} /></PageWrapper>;
  if (!athlete) return <PageWrapper><LoadingSpinner /></PageWrapper>;

  const sportCode = athlete.primary_sport?.code;
  const config = getSportConfig(sportCode);

  const TABS = [
    { key: 'summary', label: 'Overview' },
    { key: 'gameLog', label: 'Game Log' },
    { key: 'chart', label: 'Charts' },
    { key: 'radar', label: 'Skills Radar' },
    { key: 'media', label: 'Media' },
  ];

  return (
    <PageWrapper>
      <ProfileHero athlete={athlete} onDelete={handleDelete} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: editors */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-surface-800 rounded-xl border border-surface-600 p-4">
            <SkillEditor athleteId={id} />
          </div>
          <div className="bg-surface-800 rounded-xl border border-surface-600 p-4">
            <StatEditor athleteId={id} />
          </div>
        </div>

        {/* Right column: stats/charts tabs */}
        <div className="lg:col-span-2">
          <div className="bg-surface-800 rounded-xl border border-surface-600 overflow-hidden">
            {/* Tab bar */}
            <div className="flex overflow-x-auto border-b border-surface-600">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setStatsTab(tab.key)}
                  className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                    statsTab === tab.key
                      ? 'text-white border-accent bg-surface-700'
                      : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-surface-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="p-4">
              {statsTab === 'summary' && <SeasonStats athleteId={id} />}
              {statsTab === 'gameLog' && <GameLog athleteId={id} />}
              {statsTab === 'chart' && <StatChart athleteId={id} sportCode={sportCode} />}
              {statsTab === 'radar' && (
                <div>
                  <h3 className="text-sm font-semibold text-white mb-3">Skills Radar</h3>
                  <SkillRadar skills={skills} color={config.color} label={athlete.user?.full_name || 'Skills'} />
                </div>
              )}
              {statsTab === 'media' && <MediaGallery athleteId={id} />}
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
