"""Chunked upload endpoint.

Large files (>50 MB) are uploaded in fixed-size chunks. The frontend POSTs
each chunk to ``/api/athletes/<athlete_id>/upload/chunked`` along with a
shared ``chunk_id`` (uuid for the upload session), ``chunk_index`` and
``total_chunks``. Chunks are written to a per-session subdirectory under
the system temp dir. When the final chunk arrives the chunks are
reassembled into a single file, validated, and moved into the existing
media storage location.
"""

import os
import shutil
import tempfile
import logging
import uuid

from flask import request, jsonify, abort, current_app
from flask_restx import Resource
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app import db
from app.api import api
from app.models import AthleteProfile, AthleteMedia
from app.services.media_service import (
    MediaService,
    classify_extension,
    max_size_for_category,
)
from app.utils.auth import login_or_token_required


logger = logging.getLogger(__name__)


def _chunk_session_dir(chunk_id):
    """Return the on-disk dir we use to accumulate chunks for a session.

    Sanitised so a malicious chunk_id cannot escape the temp dir.
    """
    safe = secure_filename(chunk_id)
    if not safe:
        abort(400, 'Invalid chunk_id')
    base = current_app.config.get(
        'CHUNK_UPLOAD_DIR',
        os.path.join(tempfile.gettempdir(), 'pst_chunked_uploads'),
    )
    return os.path.join(base, safe)


def _coerce_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        abort(400, f"'{name}' must be an integer")


@api.route('/athletes/<string:athlete_id>/upload/chunked')
@api.param('athlete_id', 'Athlete identifier')
class ChunkedUpload(Resource):
    """Accept one chunk of a multi-part upload.

    Form fields:
        chunk_id     - shared uuid for the upload session
        chunk_index  - 0-based index of this chunk
        total_chunks - total number of chunks in the session
        filename     - original filename (sent with first chunk; cached
                       for subsequent ones)
        media_type   - optional media_type label (passed through to the
                       AthleteMedia row when finalising)
        file         - this chunk's bytes (multipart/form-data field)
    """

    @api.doc(description="Upload a single chunk of a large file")
    @login_or_token_required
    def post(self, athlete_id):
        athlete = (
            AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
            .first_or_404()
        )

        if 'file' not in request.files:
            abort(400, 'No file chunk provided')
        chunk = request.files['file']

        chunk_id = request.form.get('chunk_id') or ''
        if not chunk_id:
            abort(400, 'Missing chunk_id')

        chunk_index = _coerce_int(request.form.get('chunk_index'), 'chunk_index')
        total_chunks = _coerce_int(request.form.get('total_chunks'), 'total_chunks')
        if chunk_index < 0 or total_chunks <= 0 or chunk_index >= total_chunks:
            abort(400, 'chunk_index/total_chunks out of range')

        filename = request.form.get('filename') or chunk.filename
        if not filename:
            abort(400, 'Missing filename')

        media_type = request.form.get('media_type', 'other')

        session_dir = _chunk_session_dir(chunk_id)
        os.makedirs(session_dir, exist_ok=True)

        # Persist this chunk. We use a numeric suffix so the natural sort
        # is also the assembly order.
        chunk_path = os.path.join(session_dir, f"chunk_{chunk_index:08d}")
        chunk.save(chunk_path)

        # Stash the filename and media_type alongside the chunks so the
        # final request doesn't have to repeat them. Idempotent overwrite
        # is fine.
        with open(os.path.join(session_dir, 'meta.txt'), 'w', encoding='utf-8') as f:
            f.write(f"{filename}\n{media_type}\n{total_chunks}\n")

        existing = sorted(
            n for n in os.listdir(session_dir) if n.startswith('chunk_')
        )
        received = len(existing)

        if received < total_chunks:
            return jsonify({
                'chunk_id': chunk_id,
                'chunk_index': chunk_index,
                'received': received,
                'total_chunks': total_chunks,
                'finalized': False,
            })

        # Final chunk -> reassemble. We do this in a temporary file then
        # validate before moving into MediaService storage.
        try:
            assembled = _assemble_chunks(session_dir, existing)
        except Exception as exc:
            logger.exception("Chunk reassembly failed: %s", exc)
            shutil.rmtree(session_dir, ignore_errors=True)
            abort(500, 'Failed to reassemble upload')

        try:
            ext = os.path.splitext(filename)[1].lower()
            category = classify_extension(ext)
            if category is None:
                abort(400, f"Unsupported file type '{ext}'")

            # Build a FileStorage so we can reuse the standard validator
            # (size + magic-number sniff).
            with open(assembled, 'rb') as fh:
                fs = FileStorage(stream=fh, filename=filename)
                MediaService.validate(fs, declared_category=None)

            size = os.path.getsize(assembled)
            limit = max_size_for_category(category)
            if limit is not None and size > limit:
                abort(413,
                      f"File too large for {category}: "
                      f"{size} bytes exceeds limit of {limit} bytes.")

            # Move into final location.
            directory = MediaService.athlete_media_path(athlete_id, media_type)
            os.makedirs(directory, exist_ok=True)
            final_filename = f"{uuid.uuid4().hex}{ext}"
            final_path = os.path.join(directory, secure_filename(final_filename))
            shutil.move(assembled, final_path)

            media = AthleteMedia(
                athlete_id=athlete_id,
                media_type=media_type,
                file_path=final_path,
                original_filename=filename,
            )
            db.session.add(media)
            db.session.commit()

            logger.info(
                "Chunked upload %s finalised for athlete %s -> %s",
                chunk_id, athlete_id, final_path,
            )
            return jsonify({
                **media.to_dict(),
                'finalized': True,
                'chunk_id': chunk_id,
            })
        finally:
            shutil.rmtree(session_dir, ignore_errors=True)


def _assemble_chunks(session_dir, chunk_names):
    """Concatenate ``chunk_names`` (already sorted) into a single file
    inside ``session_dir`` and return its path."""
    out_path = os.path.join(session_dir, 'assembled.bin')
    with open(out_path, 'wb') as out:
        for name in chunk_names:
            part_path = os.path.join(session_dir, name)
            with open(part_path, 'rb') as part:
                shutil.copyfileobj(part, out, length=1024 * 1024)
    return out_path
