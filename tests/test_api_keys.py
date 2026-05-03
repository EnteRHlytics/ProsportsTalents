"""HTTP-level tests for /api/keys endpoints."""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models import ApiKey, User
from app.models.oauth import UserOAuthAccount


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def _make_user_with_token(*, token='kt-token', email='owner@example.com'):
    user = User(
        username=email.split('@')[0], email=email, first_name='K', last_name='User'
    )
    user.save()
    db.session.add(
        UserOAuthAccount(
            user_id=user.user_id,
            provider_name='test',
            provider_user_id=email,
            access_token=token,
        )
    )
    db.session.commit()
    return user


def test_list_keys_requires_auth(client):
    resp = client.get('/api/keys')
    assert resp.status_code == 401


def test_create_key_requires_auth(client):
    resp = client.post('/api/keys', json={'name': 'k'})
    assert resp.status_code == 401


def test_revoke_key_requires_auth(client):
    resp = client.delete('/api/keys/some-id')
    assert resp.status_code == 401


def test_create_key_returns_raw_only_once(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='ckey-token', email='create@example.com')

    headers = {'Authorization': 'Bearer ckey-token'}
    resp = client.post('/api/keys', json={'name': 'integration'}, headers=headers)
    assert resp.status_code == 201
    body = resp.get_json()
    raw_key = body['key']
    assert isinstance(raw_key, str) and len(raw_key) >= 32
    assert body['key_prefix'] == raw_key[:12]

    # Listing keys does NOT return the raw key value
    listed = client.get('/api/keys', headers=headers)
    assert listed.status_code == 200
    items = listed.get_json()
    assert len(items) == 1
    assert 'key' not in items[0]
    assert 'key_hash' not in items[0]
    assert items[0]['key_prefix'] == raw_key[:12]


def test_create_key_persists_hash_not_plaintext(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='hash-token', email='hash@example.com')

    headers = {'Authorization': 'Bearer hash-token'}
    resp = client.post('/api/keys', json={'name': 'hashed'}, headers=headers)
    assert resp.status_code == 201
    body = resp.get_json()
    raw = body['key']

    with app_instance.app_context():
        # The raw key should not appear anywhere in the persisted row
        record = ApiKey.query.filter_by(api_key_id=body['api_key_id']).first()
        assert record is not None
        assert record.key_hash != raw
        assert raw not in (record.key_hash or '')
        # The hash should be reproducible
        assert ApiKey.hash_key(raw) == record.key_hash


def test_create_key_validates_name(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='nm-token', email='nm@example.com')
    headers = {'Authorization': 'Bearer nm-token'}

    resp = client.post('/api/keys', json={}, headers=headers)
    assert resp.status_code == 400


def test_create_key_accepts_scopes_list(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='sc-token', email='sc@example.com')
    headers = {'Authorization': 'Bearer sc-token'}

    resp = client.post(
        '/api/keys',
        json={'name': 'scoped', 'scopes': ['read:prospects', 'write:keys']},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()['scopes'] == ['read:prospects', 'write:keys']


def test_create_key_rejects_non_list_scopes(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='bs-token', email='bs@example.com')
    headers = {'Authorization': 'Bearer bs-token'}
    resp = client.post(
        '/api/keys',
        json={'name': 'scoped', 'scopes': 'not-a-list'},
        headers=headers,
    )
    assert resp.status_code == 400


def test_list_keys_only_returns_owned(client, app_instance):
    with app_instance.app_context():
        owner = _make_user_with_token(token='own-token', email='own@example.com')
        other = User(username='other', email='other@example.com', first_name='O', last_name='X')
        other.save()
        rec, _ = ApiKey.generate(user_id=other.user_id, name='other-key')
        db.session.add(rec)
        db.session.commit()

    resp = client.get('/api/keys', headers={'Authorization': 'Bearer own-token'})
    assert resp.status_code == 200
    assert resp.get_json() == []  # owner has no keys


def test_revoke_key_marks_inactive(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='rv-token', email='rv@example.com')

    headers = {'Authorization': 'Bearer rv-token'}
    create = client.post(
        '/api/keys', json={'name': 'will-revoke'}, headers=headers
    )
    assert create.status_code == 201
    api_key_id = create.get_json()['api_key_id']

    delete_resp = client.delete(f'/api/keys/{api_key_id}', headers=headers)
    assert delete_resp.status_code == 204

    with app_instance.app_context():
        record = ApiKey.query.filter_by(api_key_id=api_key_id).first()
        assert record is not None
        assert record.is_active is False


def test_revoke_other_users_key_returns_404(client, app_instance):
    with app_instance.app_context():
        _make_user_with_token(token='atk-token', email='attacker@example.com')
        victim = User(
            username='victim', email='victim@example.com', first_name='V', last_name='X'
        )
        victim.save()
        record, _ = ApiKey.generate(user_id=victim.user_id, name='victim-key')
        db.session.add(record)
        db.session.commit()
        target_id = record.api_key_id

    resp = client.delete(
        f'/api/keys/{target_id}',
        headers={'Authorization': 'Bearer atk-token'},
    )
    assert resp.status_code == 404
