import { useEffect, useRef, useState } from 'react';

/**
 * ExportButtons — dropdown that triggers PDF/Excel exports.
 *
 * Props:
 *   type:     "athlete" | "search" | "rankings"  (required)
 *   id:       athlete_id when type === "athlete"
 *   params:   object of query params for "search" / "rankings"
 *   label:    optional override for the button label
 *
 * The component triggers a browser download via <a href> with the appropriate
 * Content-Disposition response. It works with cookie-auth out of the box. If
 * an auth token must be sent in headers, swap the anchor link for the
 * `fetchBlob` helper below.
 */
export default function ExportButtons({ type, id, params, label = 'Export' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const buildUrl = (suffix) => {
    const base = '/api/exports';
    if (type === 'athlete') {
      if (!id) throw new Error('ExportButtons requires `id` when type=athlete');
      return `${base}/athletes/${encodeURIComponent(id)}.${suffix}`;
    }
    if (type === 'search') {
      const qs = params ? new URLSearchParams(params).toString() : '';
      return `${base}/search.${suffix}${qs ? `?${qs}` : ''}`;
    }
    if (type === 'rankings') {
      const qs = params ? new URLSearchParams(params).toString() : '';
      return `${base}/rankings.${suffix}${qs ? `?${qs}` : ''}`;
    }
    throw new Error(`Unknown export type: ${type}`);
  };

  const triggerDownload = async (suffix) => {
    setOpen(false);
    const url = buildUrl(suffix);
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) {
        // eslint-disable-next-line no-console
        console.error(`Export failed (${res.status})`);
        return;
      }
      const blob = await res.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const cd = res.headers.get('Content-Disposition') || '';
      const match = /filename="?([^";]+)"?/i.exec(cd);
      const filename = match ? match[1] : `export.${suffix}`;
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('Export error', err);
    }
  };

  const buttonStyle = {
    padding: '8px 14px',
    background: 'var(--bg-surface, #ffffff)',
    color: 'var(--fg-primary, #111827)',
    fontSize: 13,
    fontWeight: 600,
    borderRadius: 'var(--radius-md, 6px)',
    border: '1px solid var(--border-default, #d1d5db)',
    cursor: 'pointer',
    fontFamily: 'var(--font-body, sans-serif)',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
  };

  const itemStyle = {
    padding: '9px 14px',
    fontSize: 13,
    color: 'var(--fg-primary, #111827)',
    background: 'transparent',
    border: 'none',
    textAlign: 'left',
    cursor: 'pointer',
    width: '100%',
    fontFamily: 'var(--font-body, sans-serif)',
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={buttonStyle}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {label}
        <span aria-hidden="true">▾</span>
      </button>
      {open && (
        <div
          role="menu"
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            right: 0,
            minWidth: 160,
            background: 'var(--bg-surface, #ffffff)',
            border: '1px solid var(--border-default, #d1d5db)',
            borderRadius: 'var(--radius-md, 6px)',
            boxShadow: '0 6px 16px rgba(15, 31, 61, 0.12)',
            zIndex: 50,
            overflow: 'hidden',
          }}
        >
          <button
            type="button"
            role="menuitem"
            style={itemStyle}
            onClick={() => triggerDownload('pdf')}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-hover, #f3f4f6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            Download PDF
          </button>
          <button
            type="button"
            role="menuitem"
            style={itemStyle}
            onClick={() => triggerDownload('xlsx')}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-hover, #f3f4f6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            Download Excel
          </button>
        </div>
      )}
    </div>
  );
}
