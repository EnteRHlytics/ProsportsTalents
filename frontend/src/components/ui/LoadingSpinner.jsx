/**
 * LoadingSpinner — simple inline spinner.
 * Minimal stub by Agent 1 to satisfy existing imports; another agent owns this dir.
 */
export default function LoadingSpinner({ size = 20, label = 'Loading…' }) {
  return (
    <div
      role="status"
      aria-label={label}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: 16,
        color: 'var(--fg-tertiary)',
        fontSize: 13,
      }}
    >
      <span
        style={{
          width: size,
          height: size,
          border: '2px solid var(--border-default)',
          borderTopColor: 'var(--orange-500)',
          borderRadius: '50%',
          display: 'inline-block',
          animation: 'spin 700ms linear infinite',
        }}
      />
      <span>{label}</span>
    </div>
  );
}
