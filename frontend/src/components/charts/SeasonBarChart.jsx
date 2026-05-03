import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

/**
 * SeasonBarChart — minimal stub by Agent 1.
 */
export default function SeasonBarChart({ data = [], dataKey, color = 'var(--orange-500)', label }) {
  if (!data.length) {
    return <div style={{ padding: 24, color: 'var(--fg-tertiary)', fontSize: 13 }}>No season data.</div>;
  }
  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 12, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--border-subtle)" strokeDasharray="3 3" />
          <XAxis dataKey="season" stroke="var(--fg-tertiary)" fontSize={11} />
          <YAxis stroke="var(--fg-tertiary)" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
              color: 'var(--fg-primary)',
            }}
          />
          <Bar dataKey={dataKey} name={label || dataKey} fill={color} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
