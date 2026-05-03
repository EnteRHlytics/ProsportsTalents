import { useEffect } from 'react';
import { X } from 'lucide-react';

/**
 * Modal — basic accessible modal. Closes on Escape and backdrop click.
 */
export default function Modal({ open, title, onClose, children, width = 560, footer }) {
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', handler);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title || 'Dialog'}
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(6, 14, 24, 0.62)',
        backdropFilter: 'blur(2px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
        animation: 'pst-modal-fade 180ms ease-out',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          color: 'var(--fg-primary)',
          width: '100%',
          maxWidth: width,
          maxHeight: 'calc(100vh - 32px)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <h3 style={{ margin: 0, fontSize: 16, color: 'var(--fg-primary)', fontWeight: 600 }}>
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--fg-tertiary)',
              cursor: 'pointer',
              display: 'inline-flex',
              padding: 4,
            }}
          >
            <X size={18} />
          </button>
        </div>
        <div style={{ padding: 18, overflowY: 'auto' }}>{children}</div>
        {footer && (
          <div
            style={{
              padding: '12px 18px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8,
              background: 'var(--bg-surface-alt)',
            }}
          >
            {footer}
          </div>
        )}
      </div>
      <style>{`
        @keyframes pst-modal-fade {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
