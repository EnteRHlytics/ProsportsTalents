import { AlertTriangle, RotateCw } from 'lucide-react';

/**
 * ErrorBanner — inline error message with optional retry.
 */
export default function ErrorBanner({ message, error, onRetry, compact = false }) {
  const text = message || error?.message || 'Something went wrong.';
  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        padding: compact ? '10px 12px' : '14px 16px',
        background: 'rgba(240, 122, 40, 0.08)',
        border: '1px solid var(--orange-500)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--orange-300)',
      }}
    >
      <AlertTriangle size={compact ? 14 : 18} style={{ flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1, fontSize: compact ? 12 : 13, lineHeight: 1.5 }}>{text}</div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          style={{
            background: 'transparent',
            border: '1px solid var(--orange-500)',
            color: 'var(--orange-300)',
            borderRadius: 'var(--radius-md)',
            padding: '4px 10px',
            fontSize: 12,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            cursor: 'pointer',
          }}
        >
          <RotateCw size={12} /> Retry
        </button>
      )}
    </div>
  );
}
