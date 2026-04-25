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
      .catch(() => setError('Failed to load athlete'))
      .finally(() => setLoading(false));
  }, [id]);

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
      .then((res) => { if (res.ok) navigate('/discover'); })
      .catch((err) => console.error('Failed to delete athlete', err));
  };

  if (loading) return <PageWrapper><LoadingSpinner /></PageWrapper>;
  if (error)   return <PageWrapper><ErrorMessage message={error} /></PageWrapper>;
  if (!athlete) return <PageWrapper><LoadingSpinner /></PageWrapper>;

  const sportCode = athlete.primary_sport?.code;
  const config = getSportConfig(sportCode);

  const TABS = [
    { key: 'summary',  label: 'Overview'     },
    { key: 'gameLog',  label: 'Game Log'      },
    { key: 'chart',    label: 'Trend Chart'   },
    { key: 'radar',    label: 'Skills Radar'  },
    { key: 'media',    label: 'Media'         },
  ];

  return (
    <PageWrapper>
      <ProfileHero athlete={athlete} onDelete={handleDelete} />

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,2fr)', gap: 20 }}>
        {/* Left: editors */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', padding: 20 }}>
            <SkillEditor athleteId={id} />
          </div>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', padding: 20 }}>
            <StatEditor athleteId={id} />
          </div>
        </div>

        {/* Right: tabs */}
        <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', overflowX: 'auto' }}>
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setStatsTab(tab.key)}
                style={{
                  flexShrink: 0,
                  padding: '13px 20px',
                  fontSize: 13,
                  fontWeight: 500,
                  background: 'none',
                  border: 'none',
                  borderBottom: `2px solid ${statsTab === tab.key ? config.color : 'transparent'}`,
                  color: statsTab === tab.key ? 'var(--fg-primary)' : 'var(--fg-tertiary)',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-body)',
                  transition: 'color var(--transition)',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div style={{ padding: 20 }}>
            {statsTab === 'summary'  && <SeasonStats athleteId={id} />}
            {statsTab === 'gameLog'  && <GameLog athleteId={id} />}
            {statsTab === 'chart'    && <StatChart athleteId={id} sportCode={sportCode} />}
            {statsTab === 'radar'    && (
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg-primary)', marginBottom: 16 }}>
                  Skills Radar — {athlete.user?.full_name || 'Athlete'}
                </div>
                <SkillRadar skills={skills} color={config.color} label={athlete.user?.full_name || 'Skills'} />
              </div>
            )}
            {statsTab === 'media'    && <MediaGallery athleteId={id} />}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
