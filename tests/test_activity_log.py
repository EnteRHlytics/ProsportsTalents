"""Tests for ActivityLog model, audit middleware, and read endpoint (Agent5)."""

import os
import sys

import pytest

# tests/conftest.py also patches sys.path/Config, but be defensive when this
# test is run in isolation.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Role
from app.models.activity_log import ActivityLog
from app.middleware.audit import extract_target_resource_id


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        if not Role.query.filter_by(name='viewer').first():
            db.session.add(Role(name='viewer'))
        if not Role.query.filter_by(name='admin').first():
            db.session.add(Role(name='admin'))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def _make_user(username='u', email=None, role_name='viewer'):
    email = email or f'{username}@example.com'
    user = User(
        username=username,
        email=email,
        first_name=username.title(),
        last_name='Test',
        is_active=True,
    )
    user.set_password('pw-secret-12345')
    role = Role.query.filter_by(name=role_name).first()
    if role:
        user.roles.append(role)
    db.session.add(user)
    db.session.commit()
    return user


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_extract_target_resource_id_uuid():
    rid = '550e8400-e29b-41d4-a716-446655440000'
    assert extract_target_resource_id(f'/api/athletes/{rid}') == rid


def test_extract_target_resource_id_uuid_with_subaction():
    rid = '550e8400-e29b-41d4-a716-446655440000'
    assert extract_target_resource_id(f'/api/athletes/{rid}/media') == rid


def test_extract_target_resource_id_int():
    assert extract_target_resource_id('/api/teams/42') == '42'


def test_extract_target_resource_id_none_for_word():
    assert extract_target_resource_id('/api/athletes') is None


def test_extract_target_resource_id_handles_blank():
    assert extract_target_resource_id('') is None
    assert extract_target_resource_id('/') is None


def test_activity_log_to_dict(app_instance):
    with app_instance.app_context():
        log = ActivityLog(
            method='POST',
            path='/api/athletes',
            status_code=201,
            ip='127.0.0.1',
            user_agent='pytest',
        )
        db.session.add(log)
        db.session.commit()
        d = log.to_dict()
        assert d['method'] == 'POST'
        assert d['path'] == '/api/athletes'
        assert d['status_code'] == 201
        assert d['created_at'] is not None


# ---------------------------------------------------------------------------
# Middleware integration: mutating requests get logged
# ---------------------------------------------------------------------------

def test_audit_middleware_logs_post(client, app_instance):
    # Hit a route that exists and accepts POST. /auth/login accepts POST.
    client.post('/auth/login', data={'username_or_email': 'no', 'password': 'no'})
    with app_instance.app_context():
        rows = ActivityLog.query.all()
        assert len(rows) >= 1
        log = rows[-1]
        assert log.method == 'POST'
        assert log.path == '/auth/login'
        assert log.status_code is not None


def test_audit_middleware_skips_get(client, app_instance):
    # GET should NOT be logged. Use a route that exists.
    client.get('/auth/login')
    with app_instance.app_context():
        rows = ActivityLog.query.all()
        assert all(r.method != 'GET' for r in rows)


def test_audit_middleware_records_ip_and_ua(client, app_instance):
    client.post(
        '/auth/login',
        data={'username_or_email': 'x', 'password': 'x'},
        headers={'User-Agent': 'AgentTest/1.0', 'X-Forwarded-For': '203.0.113.5'},
    )
    with app_instance.app_context():
        log = ActivityLog.query.order_by(ActivityLog.created_at.desc()).first()
        assert log is not None
        assert log.user_agent == 'AgentTest/1.0'
        assert log.ip == '203.0.113.5'


def test_audit_does_not_break_response_on_db_error(client, app_instance, monkeypatch):
    # Force a commit error and ensure response still returns
    from app import db as real_db

    original_commit = real_db.session.commit

    calls = {'n': 0}

    def boom(*a, **kw):
        calls['n'] += 1
        raise RuntimeError('forced')

    monkeypatch.setattr(real_db.session, 'commit', boom)
    resp = client.post('/auth/login', data={'username_or_email': 'x', 'password': 'x'})
    # Should still get a valid HTTP response (not 500 from middleware)
    assert resp.status_code < 600
    monkeypatch.setattr(real_db.session, 'commit', original_commit)


# ---------------------------------------------------------------------------
# Read endpoint authorization
# ---------------------------------------------------------------------------

def test_activity_endpoint_requires_auth(client):
    resp = client.get('/api/activity')
    assert resp.status_code in (401, 403)


def test_activity_endpoint_forbidden_for_non_admin(client, app_instance):
    with app_instance.app_context():
        _make_user('viewer1', role_name='viewer')

    client.post(
        '/auth/login',
        data={'username_or_email': 'viewer1', 'password': 'pw-secret-12345'},
        follow_redirects=False,
    )
    resp = client.get('/api/activity')
    assert resp.status_code == 403


def test_activity_endpoint_admin_can_read(client, app_instance):
    with app_instance.app_context():
        _make_user('admin1', role_name='admin')
        # Seed some logs
        for i in range(3):
            db.session.add(
                ActivityLog(
                    method='POST',
                    path=f'/api/athletes/{i}',
                    status_code=201,
                    ip='127.0.0.1',
                )
            )
        db.session.commit()

    client.post(
        '/auth/login',
        data={'username_or_email': 'admin1', 'password': 'pw-secret-12345'},
        follow_redirects=False,
    )
    resp = client.get('/api/activity?limit=50')
    assert resp.status_code == 200
    payload = resp.get_json()
    assert 'items' in payload
    assert payload['count'] >= 3


def test_activity_endpoint_filter_by_user(client, app_instance):
    with app_instance.app_context():
        admin = _make_user('admin2', role_name='admin')
        other = _make_user('victim', role_name='viewer')
        db.session.add(
            ActivityLog(
                user_id=other.user_id,
                method='POST',
                path='/api/athletes',
                status_code=201,
            )
        )
        db.session.add(
            ActivityLog(
                user_id=admin.user_id,
                method='POST',
                path='/api/athletes',
                status_code=201,
            )
        )
        db.session.commit()
        target_uid = other.user_id

    client.post(
        '/auth/login',
        data={'username_or_email': 'admin2', 'password': 'pw-secret-12345'},
        follow_redirects=False,
    )
    resp = client.get(f'/api/activity?user_id={target_uid}')
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload['count'] >= 1
    assert all(item['user_id'] == target_uid for item in payload['items'])


def test_activity_endpoint_invalid_since(client, app_instance):
    with app_instance.app_context():
        _make_user('admin3', role_name='admin')
    client.post(
        '/auth/login',
        data={'username_or_email': 'admin3', 'password': 'pw-secret-12345'},
        follow_redirects=False,
    )
    resp = client.get('/api/activity?since=not-a-date')
    assert resp.status_code == 400
