/**
 * Reusable progress bar for media uploads.
 *
 * Props:
 *  - value:   number 0..100
 *  - status:  'queued' | 'uploading' | 'done' | 'failed'
 *  - label:   optional text rendered above the bar (e.g. percentage)
 */

const STATUS_COLORS = {
  queued:    'var(--fg-tertiary, #6b7280)',
  uploading: 'var(--accent, #2563eb)',
  done:      'var(--success, #16a34a)',
  failed:    'var(--danger, #dc2626)',
};

export default function UploadProgressBar({ value = 0, status = 'queued', label }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  const color = STATUS_COLORS[status] || STATUS_COLORS.queued;

  return (
    <div
      data-testid="upload-progress-bar"
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label || `${status} ${pct}%`}
      style={{ width: '100%' }}
    >
      {label !== undefined && (
        <div style={{ fontSize: 11, color: 'var(--fg-tertiary, #6b7280)', marginBottom: 4 }}>
          {label}
        </div>
      )}
      <div
        style={{
          width: '100%',
          height: 6,
          background: 'var(--bg-surface-alt, #f3f4f6)',
          borderRadius: 3,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: color,
            transition: 'width 0.2s ease',
          }}
        />
      </div>
    </div>
  );
}
