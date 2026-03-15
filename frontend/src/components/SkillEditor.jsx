import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

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

  const inputCls = 'px-2 py-1 bg-surface-700 border border-surface-600 rounded text-sm text-slate-100 focus:outline-none focus:border-accent';

  return (
    <div>
      <h3 className="text-sm font-semibold text-white mb-3">Skills</h3>
      <ul className="skill-list space-y-2 mb-3">
        {skills.map((s) => (
          <li key={s.skill_id} className="flex items-center gap-2">
            <span className="text-slate-300 text-xs flex-1 min-w-0 truncate">{s.name}</span>
            {/* Progress bar */}
            <div className="flex-1 h-1.5 bg-surface-600 rounded-full overflow-hidden min-w-[60px]">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(100, s.level || 0)}%`,
                  background: s.level >= 90 ? '#F59E0B' : s.level >= 75 ? '#10B981' : s.level >= 60 ? '#3B82F6' : '#6B7280',
                }}
              />
            </div>
            <input
              type="number"
              value={s.level || ''}
              onChange={(e) => updateSkill(s.skill_id, Number(e.target.value))}
              className={`${inputCls} w-14 text-center`}
            />
            <button
              onClick={() => deleteSkill(s.skill_id)}
              className="text-slate-500 hover:text-red-400 transition-colors"
            >
              <X size={14} />
            </button>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input
          placeholder="Skill name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`${inputCls} flex-1`}
        />
        <input
          type="number"
          placeholder="0–100"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className={`${inputCls} w-16`}
        />
        <button
          type="button"
          onClick={addSkill}
          className="px-3 py-1 bg-accent hover:bg-indigo-500 text-white text-xs font-medium rounded transition-colors"
        >
          Add
        </button>
      </div>
    </div>
  );
}
