import { useEffect, useState } from 'react';
import { Image as ImageIcon, Video } from 'lucide-react';

/**
 * MediaGallery — minimal stub by Agent 1.
 * Tries `/api/athletes/:id/media`; degrades to "no media yet" on 404.
 */
export default function MediaGallery({ athleteId }) {
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    let alive = true;
    if (!athleteId) return;
    setLoading(true);
    fetch(`/api/athletes/${athleteId}/media`)
      .then((r) => {
        if (r.status === 404) { setEmpty(true); return []; }
        if (!r.ok) throw new Error('failed');
        return r.json();
      })
      .then((d) => { if (alive) setMedia(Array.isArray(d) ? d : (d?.items || [])); })
      .catch(() => { if (alive) setEmpty(true); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [athleteId]);

  if (loading) {
    return <div style={{ padding: 24, color: 'var(--fg-tertiary)' }}>Loading media…</div>;
  }
  if (empty || !media.length) {
    return (
      <div
        style={{
          padding: '32px 16px',
          textAlign: 'center',
          background: 'var(--bg-surface-alt)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--fg-tertiary)',
          fontSize: 13,
        }}
      >
        <ImageIcon size={28} style={{ margin: '0 auto 8px', opacity: 0.6 }} />
        <div>No media uploaded yet.</div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
        gap: 10,
      }}
    >
      {media.map((m, i) => {
        const isVideo = m.type === 'video' || /\.(mp4|webm|mov)$/i.test(m.url || '');
        return (
          <div
            key={m.id || m.url || i}
            style={{
              aspectRatio: '4/3',
              background: 'var(--bg-surface-alt)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--fg-tertiary)',
            }}
          >
            {m.url
              ? (isVideo
                  ? <Video size={28} />
                  : <img src={m.url} alt={m.caption || 'media'} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />)
              : <ImageIcon size={28} />}
          </div>
        );
      })}
    </div>
  );
}
