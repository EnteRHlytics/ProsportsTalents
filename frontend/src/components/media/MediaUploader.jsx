import { useCallback, useRef, useState } from 'react';
import { UploadCloud, X } from 'lucide-react';
import MediaTypeIcon, {
  classifyMedia,
  VIDEO_EXTENSIONS,
  IMAGE_EXTENSIONS,
  DOCUMENT_EXTENSIONS,
} from './MediaTypeIcon';
import UploadProgressBar from './UploadProgressBar';

// Per-requirements (3.3 Content Management - File Upload).
const VIDEO_MAX_BYTES    = 500 * 1024 * 1024;
const IMAGE_MAX_BYTES    = 10  * 1024 * 1024;
const DOCUMENT_MAX_BYTES = 25  * 1024 * 1024;

// Files larger than this are uploaded in 5 MB chunks.
export const CHUNK_THRESHOLD_BYTES = 50 * 1024 * 1024;
export const CHUNK_SIZE_BYTES = 5 * 1024 * 1024;
export const MAX_CHUNK_RETRIES = 3;

const ACCEPT_ATTR = [
  ...VIDEO_EXTENSIONS,
  ...IMAGE_EXTENSIONS,
  ...DOCUMENT_EXTENSIONS,
].join(',');

function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

export function validateFile(file) {
  const category = classifyMedia({ filename: file.name, mimeType: file.type });
  if (category === 'other') {
    return {
      ok: false,
      message:
        `Unsupported file type. Allowed: ${[...VIDEO_EXTENSIONS, ...IMAGE_EXTENSIONS, ...DOCUMENT_EXTENSIONS].join(', ')}`,
    };
  }
  const limits = {
    video:    VIDEO_MAX_BYTES,
    image:    IMAGE_MAX_BYTES,
    document: DOCUMENT_MAX_BYTES,
  };
  const max = limits[category];
  if (file.size > max) {
    return {
      ok: false,
      message: `File too large. ${category} files must be ≤ ${fmtBytes(max)} (got ${fmtBytes(file.size)}).`,
    };
  }
  return { ok: true, category };
}

function genId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/**
 * Single-shot upload using XMLHttpRequest so we get progress events.
 */
function uploadSingleShot({ url, file, mediaType, headers = {}, onProgress }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append('file', file);
    form.append('media_type', mediaType);

    xhr.open('POST', url);
    Object.entries(headers).forEach(([k, v]) => xhr.setRequestHeader(k, v));

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText || '{}')); }
        catch { resolve({}); }
      } else {
        let msg = `Upload failed (HTTP ${xhr.status})`;
        try {
          const body = JSON.parse(xhr.responseText || '{}');
          if (body.error || body.message) msg = body.error || body.message;
        } catch { /* ignore */ }
        reject(new Error(msg));
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.onabort = () => reject(new Error('Upload aborted'));
    xhr.send(form);
  });
}

function uploadChunk({ url, chunk, chunkIndex, totalChunks, chunkId, filename, mediaType, headers }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append('chunk_id', chunkId);
    form.append('chunk_index', String(chunkIndex));
    form.append('total_chunks', String(totalChunks));
    form.append('filename', filename);
    form.append('media_type', mediaType);
    form.append('file', chunk, `${filename}.part${chunkIndex}`);

    xhr.open('POST', url);
    Object.entries(headers || {}).forEach(([k, v]) => xhr.setRequestHeader(k, v));

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText || '{}')); }
        catch { resolve({}); }
      } else {
        let msg = `Chunk upload failed (HTTP ${xhr.status})`;
        try {
          const body = JSON.parse(xhr.responseText || '{}');
          if (body.error || body.message) msg = body.error || body.message;
        } catch { /* ignore */ }
        reject(new Error(msg));
      }
    };
    xhr.onerror = () => reject(new Error('Network error during chunk upload'));
    xhr.onabort = () => reject(new Error('Upload aborted'));
    xhr.send(form);
  });
}

async function uploadChunked({ url, file, mediaType, headers, onProgress }) {
  const chunkId = genId();
  const total = Math.ceil(file.size / CHUNK_SIZE_BYTES);
  let lastResponse = null;

  for (let i = 0; i < total; i++) {
    const start = i * CHUNK_SIZE_BYTES;
    const end = Math.min(file.size, start + CHUNK_SIZE_BYTES);
    const blob = file.slice(start, end);

    let attempt = 0;
    while (true) {
      try {
        lastResponse = await uploadChunk({
          url,
          chunk: blob,
          chunkIndex: i,
          totalChunks: total,
          chunkId,
          filename: file.name,
          mediaType,
          headers,
        });
        break;
      } catch (err) {
        attempt += 1;
        if (attempt > MAX_CHUNK_RETRIES) {
          throw new Error(`${err.message} (after ${MAX_CHUNK_RETRIES} retries)`);
        }
        // Linear back-off; tests use a stub uploader so this shouldn't slow them down.
        await new Promise((r) => setTimeout(r, 250 * attempt));
      }
    }
    if (onProgress) {
      onProgress(Math.round(((i + 1) / total) * 100));
    }
  }

  return lastResponse;
}

/**
 * MediaUploader — drag-and-drop or click-to-select multi-file uploader
 * with per-file validation, progress and status. Automatically switches
 * to chunked upload for files larger than 50 MB.
 *
 * Props:
 *   athleteId      (required) — athlete to upload media for
 *   onUploaded     called with the server response after each successful upload
 *   defaultMediaType  initial media_type label (free-form). Default: 'other'.
 *   authHeaders    optional headers (e.g. Authorization)
 */
export default function MediaUploader({
  athleteId,
  onUploaded,
  defaultMediaType = 'other',
  authHeaders = {},
}) {
  const [items, setItems] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [mediaType, setMediaType] = useState(defaultMediaType);
  const inputRef = useRef(null);

  const updateItem = useCallback((id, patch) => {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)));
  }, []);

  const enqueueAndUpload = useCallback((files) => {
    if (!athleteId) return;
    const fileArray = Array.from(files || []);
    const newItems = fileArray.map((file) => {
      const validation = validateFile(file);
      const id = genId();
      return {
        id,
        file,
        name: file.name,
        size: file.size,
        category: validation.ok ? validation.category : null,
        progress: 0,
        status: validation.ok ? 'queued' : 'failed',
        error: validation.ok ? null : validation.message,
      };
    });
    setItems((prev) => [...prev, ...newItems]);

    newItems.forEach((item) => {
      if (item.status !== 'queued') return;
      const useChunked = item.file.size > CHUNK_THRESHOLD_BYTES;
      const url = useChunked
        ? `/api/athletes/${athleteId}/upload/chunked`
        : `/api/athletes/${athleteId}/media`;

      updateItem(item.id, { status: 'uploading', progress: 0 });

      const onProgress = (p) => updateItem(item.id, { progress: p });
      const runner = useChunked ? uploadChunked : uploadSingleShot;
      runner({
        url,
        file: item.file,
        mediaType,
        headers: authHeaders,
        onProgress,
      })
        .then((resp) => {
          updateItem(item.id, { status: 'done', progress: 100, response: resp });
          if (onUploaded) onUploaded(resp);
        })
        .catch((err) => {
          updateItem(item.id, { status: 'failed', error: err.message || 'Upload failed' });
        });
    });
  }, [athleteId, authHeaders, mediaType, onUploaded, updateItem]);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer?.files?.length) enqueueAndUpload(e.dataTransfer.files);
  };
  const onSelect = (e) => {
    if (e.target.files?.length) enqueueAndUpload(e.target.files);
    e.target.value = '';
  };
  const removeItem = (id) => {
    setItems((prev) => prev.filter((it) => it.id !== id));
  };

  return (
    <div data-testid="media-uploader" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <label style={{ fontSize: 12, color: 'var(--fg-tertiary, #6b7280)' }}>
          Media type
        </label>
        <select
          value={mediaType}
          onChange={(e) => setMediaType(e.target.value)}
          aria-label="Media type"
          style={{
            fontSize: 12,
            padding: '4px 8px',
            border: '1px solid var(--border-subtle, #e5e7eb)',
            borderRadius: 4,
            background: 'var(--bg-surface, #fff)',
            color: 'var(--fg-primary, #111827)',
          }}
        >
          <option value="other">Other</option>
          <option value="highlight">Highlight</option>
          <option value="profile">Profile</option>
          <option value="document">Document</option>
          <option value="image">Image</option>
          <option value="video">Video</option>
        </select>
      </div>

      <div
        data-testid="dropzone"
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent, #2563eb)' : 'var(--border-subtle, #d1d5db)'}`,
          borderRadius: 8,
          padding: '24px 16px',
          background: isDragging ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-surface-alt, #f9fafb)',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color 0.15s ease, background 0.15s ease',
        }}
      >
        <UploadCloud size={28} style={{ marginBottom: 6, color: 'var(--fg-tertiary, #6b7280)' }} />
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--fg-primary, #111827)' }}>
          Drop files here or click to select
        </div>
        <div style={{ fontSize: 11, color: 'var(--fg-tertiary, #6b7280)', marginTop: 4 }}>
          Videos &le; 500&nbsp;MB ({VIDEO_EXTENSIONS.join(', ')}) ·
          Images &le; 10&nbsp;MB ({IMAGE_EXTENSIONS.join(', ')}) ·
          Documents &le; 25&nbsp;MB ({DOCUMENT_EXTENSIONS.join(', ')})
        </div>
        <input
          ref={inputRef}
          data-testid="file-input"
          type="file"
          multiple
          accept={ACCEPT_ATTR}
          onChange={onSelect}
          style={{ display: 'none' }}
        />
      </div>

      {items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((item) => (
            <li
              key={item.id}
              data-testid="upload-item"
              data-status={item.status}
              style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                alignItems: 'center',
                gap: 10,
                padding: 10,
                background: 'var(--bg-surface, #fff)',
                border: '1px solid var(--border-subtle, #e5e7eb)',
                borderRadius: 6,
              }}
            >
              <MediaTypeIcon
                filename={item.name}
                mediaType={item.category}
                size={20}
              />
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    color: 'var(--fg-primary, #111827)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={item.name}
                >
                  {item.name} <span style={{ color: 'var(--fg-tertiary, #6b7280)' }}>· {fmtBytes(item.size)}</span>
                </div>
                {item.status === 'failed' ? (
                  <div role="alert" style={{ fontSize: 11, color: 'var(--danger, #dc2626)', marginTop: 2 }}>
                    {item.error || 'Upload failed'}
                  </div>
                ) : (
                  <UploadProgressBar
                    value={item.progress}
                    status={item.status}
                    label={
                      item.status === 'done' ? 'Uploaded'
                      : item.status === 'uploading' ? `${item.progress}%`
                      : item.status === 'queued' ? 'Queued'
                      : null
                    }
                  />
                )}
              </div>
              <button
                type="button"
                onClick={() => removeItem(item.id)}
                aria-label={`Remove ${item.name}`}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--fg-tertiary, #6b7280)',
                  padding: 4,
                }}
              >
                <X size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
