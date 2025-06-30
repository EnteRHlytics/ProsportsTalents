import { useEffect, useState } from 'react';

export default function SkillEditor({ athleteId }) {
  const [skills, setSkills] = useState([]);
  const [name, setName] = useState('');
  const [level, setLevel] = useState('');

  const load = () => {
    fetch(`/api/athletes/${athleteId}/skills`)
      .then((res) => res.json())
      .then(setSkills)
      .catch((err) => console.error('Failed to load skills', err));
  };

  useEffect(() => {
    if (athleteId) load();
  }, [athleteId]);

  const addSkill = () => {
    fetch(`/api/athletes/${athleteId}/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, level: level ? Number(level) : undefined }),
    })
      .then((res) => res.json())
      .then((s) => {
        setSkills([...skills, s]);
        setName('');
        setLevel('');
      })
      .catch((err) => console.error('Failed to add skill', err));
  };

  const updateSkill = (skillId, newLevel) => {
    fetch(`/api/skills/${skillId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level: newLevel }),
    })
      .then((res) => res.json())
      .then((updated) => {
        setSkills(skills.map((s) => (s.skill_id === skillId ? updated : s)));
      })
      .catch((err) => console.error('Failed to update skill', err));
  };

  const deleteSkill = (skillId) => {
    fetch(`/api/skills/${skillId}`, { method: 'DELETE' })
      .then(() => setSkills(skills.filter((s) => s.skill_id !== skillId)))
      .catch((err) => console.error('Failed to delete skill', err));
  };

  return (
    <div>
      <h3>Skills</h3>
      <ul className="skill-list">
        {skills.map((s) => (
          <li key={s.skill_id}>
            <span>{s.name}</span>
            <input
              type="number"
              value={s.level || ''}
              onChange={(e) => updateSkill(s.skill_id, Number(e.target.value))}
              style={{ width: '60px', marginLeft: '0.5rem' }}
            />
            <button onClick={() => deleteSkill(s.skill_id)}>x</button>
          </li>
        ))}
      </ul>
      <div className="form-row">
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="number"
          placeholder="Level"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          style={{ width: '80px' }}
        />
        <button type="button" onClick={addSkill}>
          Add
        </button>
      </div>
    </div>
  );
}
