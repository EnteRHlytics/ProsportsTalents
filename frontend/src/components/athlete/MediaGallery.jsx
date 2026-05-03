import { useCallback, useEffect, useState } from 'react';
import { Download, Image as ImageIcon, X } from 'lucide-react';
import MediaTypeIcon, { classifyMedia } from '../media/MediaTypeIcon';

/**
 * MediaGallery — grid of media items for an athlete.
 *
 *  - Videos render with HTML5 <video controls>.
 *  - Images open in a simple lightbox modal on click.
 *  - Documents show a download link.
 *
 * Hooks to GET /api/athletes/<id>/media. Shape per item (best-effort):
 *   { media_id, file_path, original_filename, media_type, url? }
 */
export default function MediaGallery({ athleteId, refreshKey = 0 }) {
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lightboxItem, setLightboxItem] = useState(null);

  const reload = useCallback(() => {
    if (!athleteId) return;
    let alive = true;
    setLoading(true);
    setError(null);
    fetch(`/api/athletes/${athleteId}/media`)
      .then((r) => {
        if (r.status === 404) return [];
        if (!r.ok) throw new Error('Failed to load media');
        return r.json();
      })
      .then((d) => {
        if (!alive) return;
        const items = Array.isArray(d) ? d : (d?.items || []);
        setMedia(items);
      })
      .catch((e) => { if (alive) setError(e.message || 'Failed to load media'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [athleteId]);

  useEffect(() => { reload(); }, [reload, refreshKey]);

  if (loading) {
    return <div style={{ padding: 24, color: 'var(--fg-tertiary, #6b7280)' }}>Loading media…</div>;
  }
  if (error) {
    return <div role="alert" style={{ padding: 24, color: 'var(--danger, #dc2626)' }}>{error}</div>;
  }
  if (!media.length) {
    return (
      <div
        style={{
          padding: '32px 16px',
          textAlign: 'center',
          background: 'var(--bg-surface-alt, #f9fafb)',
          borderRadius: 8,
          color: 'var(--fg-tertiary, #6b7280)',
          fontSize: 13,
        }}
      >
        <ImageIcon size={28} style={{ margin: '0 auto 8px', opacity: 0.6 }} />
        <div>No media uploaded yet.</div>
      </div>
    );
  }

  return (
    <>
      <div
        data-testid="media-gallery"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gap: 12,
        }}
      >
        {media.map((m) => {
          const id = m.media_id || m.id;
          const filename = m.original_filename || m.filename || '';
          const category = classifyMedia({ filename, mimeType: m.mime_type, mediaType: m.media_type });
          const url = m.url || (id ? `/api/media/${id}/download` : null);

          if (category === 'video' && url) {
            return (
              <div
                key={id}
                data-testid="media-item-video"
                style={{
                  background: '#000',
                  borderRadius: 8,
                  overflow: 'hidden',
                  aspectRatio: '16/9',
                }}
              >
                <video
                  controls
                  preload="metadata"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  src={url}
                  aria-label={filename}
                >
                  Sorry, your browser does not support embedded video.
                </video>
              </div>
            );
          }

          if (category === 'image' && url) {
            return (
              <button
                key={id}
                type="button"
                data-testid="media-item-image"
                onClick={() => setLightboxItem({ url, name: filename })}
                style={{
                  padding: 0,
                  border: 'none',
                  borderRadius: 8,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  aspectRatio: '4/3',
                  background: 'var(--bg-surface-alt, #f3f4f6)',
                }}
                aria-label={`Open ${filename || 'image'}`}
              >
                <img
                  src={url}
                  alt={filename || 'media'}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </button>
            );
          }

          return (
            <a
              key={id}
              href={url || '#'}
              download={filename || true}
              data-testid="media-item-document"
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 16,
                gap: 8,
                aspectRatio: '4/3',
                background: 'var(--bg-surface-alt, #f3f4f6)',
                borderRadius: 8,
                color: 'var(--fg-primary, #111827)',
                textDecoration: 'none',
                fontSize: 12,
              }}
            >
              <MediaTypeIcon filename={filename} mediaType={m.media_type} size={32} />
              <span
                style={{
                  textAlign: 'center',
                  width: '100%',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={filename}
              >
                {filename || 'Document'}
              </span>
              <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center', color: 'var(--accent, #2563eb)' }}>
                <Download size={14} /> Download
              </span>
            </a>
          );
        })}
      </div>

      {lightboxItem && (
        <div
          data-testid="lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={lightboxItem.name || 'Image preview'}
          onClick={() => setLightboxItem(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 24,
          }}
        >
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setLightboxItem(null); }}
            aria-label="Close preview"
            style={{
              position: 'absolute',
              top: 16,
              right: 16,
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              color: '#fff',
              borderRadius: 999,
              width: 36,
              height: 36,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={18} />
          </button>
          <img
            src={lightboxItem.url}
            alt={lightboxItem.name || 'preview'}
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '90vw', maxHeight: '90vh', objectFit: 'contain', borderRadius: 6 }}
          />
        </div>
      )}
    </>
  );
}
