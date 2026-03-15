import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PageWrapper from './layout/PageWrapper';

const SPORTS = ['NBA', 'NFL', 'MLB', 'NHL', 'SOC'];

export default function AthleteForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [nationality, setNationality] = useState('');
  const [sport, setSport] = useState('');
  const [position, setPosition] = useState('');
  const [team, setTeam] = useState('');
  const [rating, setRating] = useState('');
  const [jerseyNumber, setJerseyNumber] = useState('');
  const [bio, setBio] = useState('');

  useEffect(() => {
    if (isEdit) {
      fetch(`/api/athletes/${id}`)
        .then((res) => res.json())
        .then((data) => {
          setFirstName(data.user.first_name || '');
          setLastName(data.user.last_name || '');
          setDob(data.date_of_birth || '');
          setNationality(data.nationality || '');
          setSport(data.primary_sport?.code || '');
          setPosition(data.primary_position?.name || '');
          setTeam(data.current_team?.name || '');
          setRating(data.overall_rating ?? '');
          setJerseyNumber(data.jersey_number || '');
          setBio(data.bio || '');
        })
        .catch((err) => console.error('Failed to fetch athlete', err));
    }
  }, [isEdit, id]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      first_name: firstName,
      last_name: lastName,
      date_of_birth: dob,
      nationality,
      sport,
      position,
      team,
      overall_rating: rating ? Number(rating) : undefined,
      jersey_number: jerseyNumber || undefined,
      bio,
    };
    const url = isEdit ? `/api/athletes/${id}` : '/api/athletes';
    const method = isEdit ? 'PUT' : 'POST';
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        const athleteId = data.athlete_id || id;
        navigate(`/athletes/${athleteId}`);
      })
      .catch((err) => console.error('Failed to save athlete', err));
  };

  const inputCls =
    'w-full px-3 py-2 bg-surface-800 border border-surface-600 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent';
  const labelCls = 'block text-xs text-slate-400 mb-1 font-medium';

  return (
    <PageWrapper>
      <div className="max-w-xl mx-auto">
        <h2 className="text-2xl font-bold text-white mb-6">{isEdit ? 'Edit Athlete' : 'New Athlete'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4 bg-surface-800 rounded-xl border border-surface-600 p-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>First Name</label>
              <input className={inputCls} value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div>
              <label className={labelCls}>Last Name</label>
              <input className={inputCls} value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Date of Birth</label>
              <input type="date" className={inputCls} value={dob} onChange={(e) => setDob(e.target.value)} />
            </div>
            <div>
              <label className={labelCls}>Nationality</label>
              <input className={inputCls} value={nationality} onChange={(e) => setNationality(e.target.value)} placeholder="e.g. American" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Sport</label>
              <select className={inputCls} value={sport} onChange={(e) => setSport(e.target.value)}>
                <option value="">Select sport</option>
                {SPORTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Position</label>
              <input className={inputCls} value={position} onChange={(e) => setPosition(e.target.value)} placeholder="e.g. Point Guard" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Team</label>
              <input className={inputCls} value={team} onChange={(e) => setTeam(e.target.value)} placeholder="Team name" />
            </div>
            <div>
              <label className={labelCls}>Jersey Number</label>
              <input className={inputCls} value={jerseyNumber} onChange={(e) => setJerseyNumber(e.target.value)} placeholder="#" />
            </div>
          </div>

          <div>
            <label className={labelCls}>Overall Rating (0–99)</label>
            <input
              type="number"
              min={0}
              max={99}
              className={inputCls}
              value={rating}
              onChange={(e) => setRating(e.target.value)}
              placeholder="e.g. 85"
            />
          </div>

          <div>
            <label className={labelCls}>Bio</label>
            <textarea
              rows={3}
              className={`${inputCls} resize-none`}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Short bio..."
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 bg-accent hover:bg-indigo-500 text-white font-semibold rounded-lg transition-colors"
          >
            {isEdit ? 'Save Changes' : 'Create Athlete'}
          </button>
        </form>
      </div>
    </PageWrapper>
  );
}
