import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function AthleteForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [nationality, setNationality] = useState('');

  useEffect(() => {
    if (isEdit) {
      fetch(`/api/athletes/${id}`)
        .then((res) => res.json())
        .then((data) => {
          setFirstName(data.user.first_name || '');
          setLastName(data.user.last_name || '');
          setDob(data.date_of_birth || '');
          setNationality(data.nationality || '');
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

  return (
    <div className="container">
      <h2>{isEdit ? 'Edit Athlete' : 'New Athlete'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label>First Name</label>
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Last Name</label>
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Date of Birth</label>
          <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Nationality</label>
          <input value={nationality} onChange={(e) => setNationality(e.target.value)} />
        </div>
        <button type="submit">Save</button>
      </form>
    </div>
  );
}
