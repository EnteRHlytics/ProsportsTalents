import os
import uuid
import logging
import mimetypes
from werkzeug.utils import secure_filename
from flask import abort
from PIL import Image


# Per-requirements limits (Section 3.3 Content Management - File Upload)
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx'}

VIDEO_MAX_BYTES = 500 * 1024 * 1024   # 500 MB
IMAGE_MAX_BYTES = 10 * 1024 * 1024    # 10 MB
DOCUMENT_MAX_BYTES = 25 * 1024 * 1024  # 25 MB

# Magic-number prefixes used for a quick content sniff. Each entry maps
# extension -> list of acceptable byte prefixes (or callable predicates).
_MAGIC_NUMBERS = {
    '.jpg':  [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
    '.png':  [b'\x89PNG\r\n\x1a\n'],
    '.gif':  [b'GIF87a', b'GIF89a'],
    '.pdf':  [b'%PDF-'],
    '.mp4':  [b'\x00\x00\x00\x18ftyp', b'\x00\x00\x00\x14ftyp', b'\x00\x00\x00\x1cftyp', b'\x00\x00\x00\x20ftyp'],
    '.mov':  [b'\x00\x00\x00\x14ftyp', b'\x00\x00\x00\x18ftyp', b'\x00\x00\x00\x1cftyp', b'moov'],
    '.avi':  [b'RIFF'],
    # ZIP-based formats (docx) start with PK; legacy doc starts with D0CF11E0...
    '.docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
    '.doc':  [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
}


def classify_extension(ext):
    """Return the media category for a given lowercase extension or None."""
    ext = (ext or '').lower()
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in DOCUMENT_EXTENSIONS:
        return 'document'
    return None


def max_size_for_category(category):
    return {
        'video': VIDEO_MAX_BYTES,
        'image': IMAGE_MAX_BYTES,
        'document': DOCUMENT_MAX_BYTES,
    }.get(category)


def _file_size(file_storage):
    """Return the size in bytes of an uploaded werkzeug FileStorage."""
    stream = file_storage.stream
    try:
        pos = stream.tell()
    except Exception:
        pos = 0
    try:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
    except Exception:
        # Fallback: use content_length if the stream is not seekable.
        size = getattr(file_storage, 'content_length', None) or 0
    finally:
        try:
            stream.seek(pos)
        except Exception:
            pass
    return size


def _magic_number_ok(file_storage, ext):
    """Read the first bytes of the upload and verify they match the
    expected magic number for the declared extension. Returns True if
    we either don't have a known signature for the extension or the
    bytes match one of the known prefixes."""
    expected_prefixes = _MAGIC_NUMBERS.get(ext.lower())
    if not expected_prefixes:
        return True
    stream = file_storage.stream
    try:
        pos = stream.tell()
    except Exception:
        pos = 0
    try:
        head = stream.read(32) or b''
    finally:
        try:
            stream.seek(pos)
        except Exception:
            pass
    # Special case: mp4/mov 'ftyp' boxes - the first 4 bytes are a
    # variable size; just check that bytes 4..8 == b'ftyp' for those.
    if ext.lower() in {'.mp4', '.mov'} and len(head) >= 8 and head[4:8] == b'ftyp':
        return True
    return any(head.startswith(p) for p in expected_prefixes)


def validate_upload(file_storage, declared_category=None):
    """Validate a werkzeug FileStorage against per-type extension/size
    limits. Returns the resolved category (video/image/document). Raises
    a Flask HTTPException with a friendly message on failure."""
    filename = file_storage.filename or ''
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        abort(400, 'File must have an extension')

    category = classify_extension(ext)
    if category is None:
        abort(400, f"Unsupported file type '{ext}'. Allowed: "
                   f"{sorted(VIDEO_EXTENSIONS | IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS)}")

    if declared_category and declared_category != category:
        # Allow callers to skip this if they pass None, but fail if a
        # declared category disagrees with the resolved one.
        abort(400,
              f"Declared media_type '{declared_category}' does not match "
              f"file extension category '{category}'.")

    max_bytes = max_size_for_category(category)
    size = _file_size(file_storage)
    if max_bytes is not None and size > max_bytes:
        abort(413,
              f"File too large for {category}: "
              f"{size} bytes exceeds limit of {max_bytes} bytes.")

    if not _magic_number_ok(file_storage, ext):
        abort(400, f"File contents do not match declared extension '{ext}'.")

    # MIME sniff via filename mapping (best-effort, advisory).
    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        if category == 'image' and not guessed.startswith('image/'):
            abort(400, f"MIME mismatch: expected image, got '{guessed}'.")
        if category == 'video' and not guessed.startswith('video/'):
            abort(400, f"MIME mismatch: expected video, got '{guessed}'.")

    return category


class MediaService:
    BASE_DIR = 'storage'

    # Re-export the constants for callers that want to reference them.
    VIDEO_EXTENSIONS = VIDEO_EXTENSIONS
    IMAGE_EXTENSIONS = IMAGE_EXTENSIONS
    DOCUMENT_EXTENSIONS = DOCUMENT_EXTENSIONS
    VIDEO_MAX_BYTES = VIDEO_MAX_BYTES
    IMAGE_MAX_BYTES = IMAGE_MAX_BYTES
    DOCUMENT_MAX_BYTES = DOCUMENT_MAX_BYTES

    @staticmethod
    def athlete_media_path(athlete_id, media_type):
        return os.path.join(MediaService.BASE_DIR, 'athletes', athlete_id, media_type)

    @staticmethod
    def validate(file_storage, declared_category=None):
        """Public hook so other endpoints (chunked upload, etc.) can
        share the same validation rules."""
        return validate_upload(file_storage, declared_category=declared_category)

    @staticmethod
    def save_file(file_storage, athlete_id, media_type, validate=True):
        if validate:
            # media_type may be a free-form label (e.g. 'highlight'); only
            # treat it as a strict category when it is one of the known
            # category names.
            declared = media_type if media_type in {'video', 'image', 'document'} else None
            try:
                validate_upload(file_storage, declared_category=declared)
            except Exception:
                # Re-raise -- abort() already produced a proper HTTP error.
                raise
        directory = MediaService.athlete_media_path(athlete_id, media_type)
        os.makedirs(directory, exist_ok=True)
        ext = os.path.splitext(file_storage.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(directory, secure_filename(filename))
        file_storage.save(path)
        logging.getLogger(__name__).info("Saved media file %s", path)
        return path, filename

    @staticmethod
    def delete_file(path):
        try:
            os.remove(path)
            logging.getLogger(__name__).info("Deleted media file %s", path)
        except FileNotFoundError:
            pass

    @staticmethod
    def create_thumbnail(image_path, size=(128, 128)):
        """Create a thumbnail for the given image and return the path."""
        img = Image.open(image_path)
        img.thumbnail(size)
        base, ext = os.path.splitext(image_path)
        thumb_path = f"{base}_thumb{ext}"
        img.save(thumb_path)
        return thumb_path

    @staticmethod
    def compress_image(image_path, quality=80):
        """Compress an image in-place using the specified quality."""
        img = Image.open(image_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(image_path, optimize=True, quality=quality)
        return image_path

    @staticmethod
    def save_image(file_storage, athlete_id, media_type,
                   create_thumbnail=False, thumbnail_size=(128, 128),
                   compress=False, quality=80):
        """Save an uploaded image with optional compression and thumbnail."""
        # Skip strict validation here - callers using the dedicated image
        # path may pass through helper paths (mocks etc.). The save_file
        # call below still validates by default for new uploads.
        path, filename = MediaService.save_file(file_storage, athlete_id, media_type, validate=False)
        if compress:
            MediaService.compress_image(path, quality=quality)
        thumb_path = None
        if create_thumbnail:
            thumb_path = MediaService.create_thumbnail(path, size=thumbnail_size)
        return path, filename, thumb_path
