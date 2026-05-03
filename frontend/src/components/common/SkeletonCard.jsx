/**
 * SkeletonCard — placeholder card while data is loading.
 */
export default function SkeletonCard({ height = 140, style }) {
  return (
    <div
      style={{
        height,
        borderRadius: 'var(--radius-lg)',
        background: 'linear-gradient(90deg, var(--bg-surface) 0%, var(--bg-surface-alt) 50%, var(--bg-surface) 100%)',
        backgroundSize: '200% 100%',
        animation: 'pst-skeleton-shimmer 1.4s ease-in-out infinite',
        border: '1px solid var(--border-subtle)',
        ...style,
      }}
    >
      <style>{`
        @keyframes pst-skeleton-shimmer {
          0%   { background-position: 0% 0%; }
          100% { background-position: -200% 0%; }
        }
      `}</style>
    </div>
  );
}

export function SkeletonGrid({ count = 6, ...rest }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: 16,
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} {...rest} />
      ))}
    </div>
  );
}
