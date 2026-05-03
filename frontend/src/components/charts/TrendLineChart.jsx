import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

/**
 * TrendLineChart — minimal stub by Agent 1.
 */
export default function TrendLineChart({ data = [], dataKey, color = 'var(--orange-500)', label }) {
  if (!data.length) {
    return <div style={{ padding: 24, color: 'var(--fg-tertiary)', fontSize: 13 }}>No trend data.</div>;
  }
  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 12, right: 16, bottom: 8, left: 0 }}>
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
          <Line type="monotone" dataKey={dataKey} name={label || dataKey} stroke={color} strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
