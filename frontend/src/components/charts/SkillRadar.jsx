import { ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from 'recharts';

/**
 * SkillRadar — radar chart for skill levels.
 * Used by AthleteProfile and ComparePage.
 */
export default function SkillRadar({ skills = [], color = 'var(--orange-500)', label = 'Skills', height = 320 }) {
  // Accept either [{name, level}] or [{skill, value}] etc.
  const data = (skills || []).map((s) => ({
    name: s.name || s.skill || s.label || '—',
    value: Number(s.level ?? s.value ?? s.score ?? 0) || 0,
  }));

  if (!data.length) {
    return (
      <div
        style={{
          padding: 24,
          textAlign: 'center',
          color: 'var(--fg-tertiary)',
          fontSize: 13,
          background: 'var(--bg-surface-alt)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        No skills tracked yet.
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="var(--border-default)" />
          <PolarAngleAxis dataKey="name" tick={{ fill: 'var(--fg-secondary)', fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--fg-tertiary)', fontSize: 10 }} stroke="var(--border-default)" />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
              color: 'var(--fg-primary)',
            }}
          />
          <Radar name={label} dataKey="value" stroke={color} fill={color} fillOpacity={0.35} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * MultiSkillRadar — overlays multiple athletes for compare.
 *
 * `series`: [{ label, color, skills: [{name, level}] }]
 */
export function MultiSkillRadar({ series = [], height = 360 }) {
  // Build merged dataset keyed by skill name.
  const allNames = Array.from(new Set(
    series.flatMap((s) => (s.skills || []).map((sk) => sk.name || sk.skill || sk.label))
  )).filter(Boolean);

  if (!allNames.length || !series.length) {
    return (
      <div style={{ padding: 24, color: 'var(--fg-tertiary)', textAlign: 'center', fontSize: 13 }}>
        No comparable skill data.
      </div>
    );
  }

  const data = allNames.map((name) => {
    const row = { name };
    series.forEach((s, i) => {
      const match = (s.skills || []).find((sk) => (sk.name || sk.skill || sk.label) === name);
      row[s.label || `series_${i}`] = Number(match?.level ?? match?.value ?? 0) || 0;
    });
    return row;
  });

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
          <PolarGrid stroke="var(--border-default)" />
          <PolarAngleAxis dataKey="name" tick={{ fill: 'var(--fg-secondary)', fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--fg-tertiary)', fontSize: 10 }} stroke="var(--border-default)" />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
              color: 'var(--fg-primary)',
            }}
          />
          {series.map((s, i) => (
            <Radar
              key={s.label || i}
              name={s.label || `Athlete ${i + 1}`}
              dataKey={s.label || `series_${i}`}
              stroke={s.color || 'var(--orange-500)'}
              fill={s.color || 'var(--orange-500)'}
              fillOpacity={0.25}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
