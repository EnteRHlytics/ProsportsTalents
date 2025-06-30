import { useParams, Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import SkillEditor from '../components/SkillEditor';
import StatEditor from '../components/StatEditor';

export default function AthleteProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [athlete, setAthlete] = useState(null);

  useEffect(() => {
    fetch(`/api/athletes/${id}`)
      .then((res) => res.json())
      .then((data) => setAthlete(data))
      .catch((err) => console.error('Failed to fetch athlete', err));
  }, [id]);

  const handleDelete = () => {
    if (!window.confirm('Delete this athlete?')) return;
    fetch(`/api/athletes/${id}`, { method: 'DELETE' })
      .then((res) => {
        if (res.ok) navigate('/');
      })
      .catch((err) => console.error('Failed to delete athlete', err));
  };

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
    </div>
    </div>
  );
}
