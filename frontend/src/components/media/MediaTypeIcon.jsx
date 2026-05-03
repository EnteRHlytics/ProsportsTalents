import { FileText, Film, Image as ImageIcon, File } from 'lucide-react';

export const VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov'];
export const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif'];
export const DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx'];

/**
 * Resolve the broad media category for a filename / extension / mime type.
 * Returns one of: 'video' | 'image' | 'document' | 'other'.
 */
export function classifyMedia({ filename, mimeType, mediaType } = {}) {
  if (mediaType && ['video', 'image', 'document'].includes(mediaType)) {
    return mediaType;
  }
  const lowerName = (filename || '').toLowerCase();
  const ext = lowerName.includes('.') ? lowerName.slice(lowerName.lastIndexOf('.')) : '';
  if (VIDEO_EXTENSIONS.includes(ext)) return 'video';
  if (IMAGE_EXTENSIONS.includes(ext)) return 'image';
  if (DOCUMENT_EXTENSIONS.includes(ext)) return 'document';
  if (mimeType) {
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('image/')) return 'image';
    if (
      mimeType === 'application/pdf' ||
      mimeType === 'application/msword' ||
      mimeType.startsWith('application/vnd.openxmlformats-officedocument')
    ) {
      return 'document';
    }
  }
  return 'other';
}

/**
 * Small lucide-react icon helper that renders a category-appropriate icon.
 * Forwards any extra props to the underlying lucide component.
 */
export default function MediaTypeIcon({
  filename,
  mimeType,
  mediaType,
  size = 18,
  ...rest
}) {
  const category = classifyMedia({ filename, mimeType, mediaType });
  const props = { size, 'aria-label': `${category} file`, ...rest };
  switch (category) {
    case 'video':    return <Film {...props} />;
    case 'image':    return <ImageIcon {...props} />;
    case 'document': return <FileText {...props} />;
    default:         return <File {...props} />;
  }
}
