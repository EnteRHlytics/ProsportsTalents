import { Inbox } from 'lucide-react';

/**
 * EmptyState — shown when an API returns no results / 404 / "no data yet".
 */
export default function EmptyState({
  title = 'No data yet',
  description = 'Nothing has been added here.',
  icon = null,
  action = null,
  compact = false,
}) {
  const Icon = icon || (() => <Inbox size={compact ? 24 : 36} />);
  return (
    <div
      role="status"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: compact ? '24px 16px' : '48px 16px',
        background: 'var(--bg-surface)',
        border: '1px dashed var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        color: 'var(--fg-tertiary)',
        gap: 10,
      }}
    >
      <div
        style={{
          width: compact ? 40 : 56,
          height: compact ? 40 : 56,
          borderRadius: '50%',
          background: 'var(--bg-surface-alt)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--fg-tertiary)',
        }}
      >
        <Icon />
      </div>
      <div style={{ fontSize: compact ? 14 : 16, color: 'var(--fg-primary)', fontWeight: 600 }}>
        {title}
      </div>
      {description && (
        <div style={{ fontSize: 13, color: 'var(--fg-tertiary)', maxWidth: 420 }}>
          {description}
        </div>
      )}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}
