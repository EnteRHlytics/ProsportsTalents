"""Tests for the chunked-upload endpoint."""

import io
import json
import os
import sys
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, AthleteProfile, AthleteMedia
from app.models.oauth import UserOAuthAccount
from app.services.media_service import MediaService


# A tiny but signature-correct PDF payload used for valid uploads.
_PDF_BYTES = b'%PDF-1.4\n%' + (b'\xe2\xe3\xcf\xd3') + (b'\n0 obj\n<<>>\nendobj\n' * 20)


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setattr(MediaService, 'BASE_DIR', str(tmp_path / 'storage'))
    app = create_app('testing')
    app.config['CHUNK_UPLOAD_DIR'] = str(tmp_path / 'chunks')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture
def auth_headers(app_instance):
    with app_instance.app_context():
        user = User(username='cu', email='cu@example.com', first_name='C', last_name='U')
        user.save()
        oauth = UserOAuthAccount(
            user_id=user.user_id,
            provider_name='test',
            provider_user_id='cu123',
            access_token='cutoken',
        )
        db.session.add(oauth)
        db.session.commit()
    return {'Authorization': 'Bearer cutoken'}


def _create_athlete():
    user = User(
        username=str(uuid.uuid4()),
        email=f'{uuid.uuid4()}@example.com',
        first_name='F', last_name='L',
    )
    user.save()
    athlete = AthleteProfile(
        user_id=user.user_id,
        date_of_birth=date.fromisoformat('2000-01-01'),
    )
    athlete.save()
    return athlete


def _post_chunk(client, athlete_id, chunk_id, idx, total, payload, filename, headers,
                media_type='document'):
    data = {
        'chunk_id': chunk_id,
        'chunk_index': str(idx),
        'total_chunks': str(total),
        'filename': filename,
        'media_type': media_type,
        'file': (io.BytesIO(payload), f'part-{idx}'),
    }
    return client.post(
        f'/api/athletes/{athlete_id}/upload/chunked',
        data=data,
        headers=headers,
        content_type='multipart/form-data',
    )


def test_finalises_after_last_chunk(client, app_instance, auth_headers):
    athlete = _create_athlete()
    chunk_id = uuid.uuid4().hex
    half = len(_PDF_BYTES) // 2
    parts = [_PDF_BYTES[:half], _PDF_BYTES[half:]]

    r0 = _post_chunk(client, athlete.athlete_id, chunk_id, 0, 2, parts[0], 'big.pdf', auth_headers)
    assert r0.status_code == 200
    body0 = json.loads(r0.data)
    assert body0['finalized'] is False
    assert body0['received'] == 1

    r1 = _post_chunk(client, athlete.athlete_id, chunk_id, 1, 2, parts[1], 'big.pdf', auth_headers)
    assert r1.status_code == 200
    body1 = json.loads(r1.data)
    assert body1['finalized'] is True
    assert body1['original_filename'] == 'big.pdf'

    with app_instance.app_context():
        rows = AthleteMedia.query.filter_by(athlete_id=athlete.athlete_id).all()
        assert len(rows) == 1
        assert os.path.exists(rows[0].file_path)
        with open(rows[0].file_path, 'rb') as fh:
            assert fh.read() == _PDF_BYTES


def test_intermediate_chunk_does_not_create_media(client, app_instance, auth_headers):
    athlete = _create_athlete()
    chunk_id = uuid.uuid4().hex
    r = _post_chunk(client, athlete.athlete_id, chunk_id, 0, 3, b'aaaa', 'x.pdf', auth_headers)
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['finalized'] is False
    with app_instance.app_context():
        assert AthleteMedia.query.count() == 0


def test_rejects_unsupported_extension(client, app_instance, auth_headers):
    athlete = _create_athlete()
    chunk_id = uuid.uuid4().hex
    payload = b'just some bytes'
    r = _post_chunk(client, athlete.athlete_id, chunk_id, 0, 1, payload, 'evil.exe', auth_headers)
    assert r.status_code == 400
    with app_instance.app_context():
        assert AthleteMedia.query.count() == 0


def test_rejects_missing_chunk_id(client, auth_headers):
    athlete = _create_athlete()
    data = {
        'chunk_index': '0',
        'total_chunks': '1',
        'filename': 'a.pdf',
        'file': (io.BytesIO(_PDF_BYTES), 'p'),
    }
    r = client.post(
        f'/api/athletes/{athlete.athlete_id}/upload/chunked',
        data=data, headers=auth_headers, content_type='multipart/form-data',
    )
    assert r.status_code == 400


def test_unknown_athlete_returns_404(client, auth_headers):
    chunk_id = uuid.uuid4().hex
    data = {
        'chunk_id': chunk_id,
        'chunk_index': '0',
        'total_chunks': '1',
        'filename': 'a.pdf',
        'file': (io.BytesIO(_PDF_BYTES), 'p'),
    }
    r = client.post(
        '/api/athletes/does-not-exist/upload/chunked',
        data=data, headers=auth_headers, content_type='multipart/form-data',
    )
    assert r.status_code == 404
