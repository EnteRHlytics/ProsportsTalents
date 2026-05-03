"""Tests for the per-user saved-searches CRUD endpoints.

These tests intentionally guard against unrelated incomplete modules
in the wider codebase by pre-stubbing their imports before bringing
up the Flask app, so failures elsewhere do not mask the behaviour
under test here.
"""

import os
import sys
import json
import types
import uuid
import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ---------------------------------------------------------------------------
# Stub out optional/in-progress sibling modules so the application package
# can import successfully even when other agents have not yet landed their
# code. These stubs only register placeholder symbols where the package
# ``__init__`` files attempt to import names that may not exist yet.
# ---------------------------------------------------------------------------
def _ensure_stub(name, attrs=None):
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    for attr, value in (attrs or {}).items():
        setattr(mod, attr, value)
    sys.modules[name] = mod


class _Placeholder:
    """Inert placeholder used for symbols other agents will provide."""


_ensure_stub('app.models.prospect', {
    'ProspectLeague': _Placeholder,
    'MinorLeagueTeam': _Placeholder,
    'Prospect': _Placeholder,
    'ProspectStat': _Placeholder,
})
_ensure_stub('app.models.api_key', {'ApiKey': _Placeholder})
_ensure_stub('app.api.keys')
_ensure_stub('app.api.prospects')


def _noop_decorator(fn=None, *a, **kw):
    if callable(fn):
        return fn

    def _wrap(inner):
        return inner

    return _wrap


_ensure_stub('app.utils.security', {'require_api_key': _noop_decorator})


# ---------------------------------------------------------------------------
# App / DB setup
# ---------------------------------------------------------------------------
from app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402
from app.models.oauth import UserOAuthAccount  # noqa: E402
from app.models.saved_search import SavedSearch  # noqa: E402
# Import saved_searches API module so its routes are registered with the
# Flask-RESTX namespace before the app boots (the project's main
# ``app/api/__init__.py`` does not yet import it — see MERGE_NOTES.md).
from app.api import saved_searches as _saved_searches_api  # noqa: F401, E402


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    monkeypatch.setenv('SECRET_KEY', 'test-secret')

    # The shared ``Config`` class enables PostgreSQL-only engine
    # options (pool_size / max_overflow) that SQLite rejects, so we
    # neutralise them on the Config class before ``create_app`` wires
    # SQLAlchemy up. Patched only for the duration of this fixture.
    from config import Config, TestingConfig
    monkeypatch.setattr(Config, 'SQLALCHEMY_ENGINE_OPTIONS', {}, raising=False)
    monkeypatch.setattr(TestingConfig, 'SQLALCHEMY_ENGINE_OPTIONS', {}, raising=False)

    app = create_app('testing')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    app.config['LOGIN_DISABLED'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def _make_user(username_suffix=''):
    suffix = username_suffix or uuid.uuid4().hex[:8]
    user = User(
        username=f'searcher_{suffix}',
        email=f'searcher_{suffix}@example.com',
        first_name='Search',
        last_name='User',
    )
    user.save()
    return user


def _make_auth_headers(user, token=None):
    token = token or f'tok-{uuid.uuid4().hex}'
    oauth = UserOAuthAccount(
        user_id=user.user_id,
        provider_name='test',
        provider_user_id=f'pid-{uuid.uuid4().hex}',
        access_token=token,
    )
    db.session.add(oauth)
    db.session.commit()
    return {'Authorization': f'Bearer {token}'}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_list_requires_auth(client):
    resp = client.get('/api/saved-searches')
    assert resp.status_code == 401


def test_create_requires_auth(client):
    resp = client.post('/api/saved-searches', json={'name': 'x'})
    assert resp.status_code == 401


def test_create_and_list_saved_search(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    payload = {
        'name': 'NBA point guards',
        'params': {'sport': 'NBA', 'position': 'PG', 'min_age': 21},
    }
    resp = client.post('/api/saved-searches', json=payload, headers=headers)
    assert resp.status_code == 201, resp.data
    created = json.loads(resp.data)
    assert created['name'] == 'NBA point guards'
    assert created['params'] == payload['params']
    assert 'id' in created and created['id']

    resp = client.get('/api/saved-searches', headers=headers)
    assert resp.status_code == 200
    items = json.loads(resp.data)
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]['id'] == created['id']
    assert items[0]['params']['sport'] == 'NBA'


def test_create_rejects_missing_name(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    resp = client.post('/api/saved-searches', json={'params': {}}, headers=headers)
    assert resp.status_code == 400


def test_create_rejects_duplicate_name_for_same_user(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    body = {'name': 'Top NHL', 'params': {'filter': 'top', 'sport': 'NHL'}}
    r1 = client.post('/api/saved-searches', json=body, headers=headers)
    assert r1.status_code == 201
    r2 = client.post('/api/saved-searches', json=body, headers=headers)
    assert r2.status_code == 409


def test_get_returns_only_owned_search(app_instance):
    with app_instance.app_context():
        owner = _make_user('owner')
        other = _make_user('other')
        owner_headers = _make_auth_headers(owner)
        other_headers = _make_auth_headers(other)

    owner_client = app_instance.test_client()
    other_client = app_instance.test_client()

    # Owner creates.
    r = owner_client.post(
        '/api/saved-searches',
        json={'name': 'mine', 'params': {'q': 'hello'}},
        headers=owner_headers,
    )
    assert r.status_code == 201
    search_id = json.loads(r.data)['id']

    # Owner can retrieve.
    r = owner_client.get(f'/api/saved-searches/{search_id}', headers=owner_headers)
    assert r.status_code == 200
    assert json.loads(r.data)['id'] == search_id

    # Other user cannot retrieve.
    r = other_client.get(f'/api/saved-searches/{search_id}', headers=other_headers)
    assert r.status_code == 404


def test_update_saved_search(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    r = client.post(
        '/api/saved-searches',
        json={'name': 'old', 'params': {'sport': 'MLB'}},
        headers=headers,
    )
    sid = json.loads(r.data)['id']

    r = client.put(
        f'/api/saved-searches/{sid}',
        json={'name': 'new', 'params': {'sport': 'NFL', 'min_age': 25}},
        headers=headers,
    )
    assert r.status_code == 200, r.data
    body = json.loads(r.data)
    assert body['name'] == 'new'
    assert body['params'] == {'sport': 'NFL', 'min_age': 25}


def test_update_only_params(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    r = client.post(
        '/api/saved-searches',
        json={'name': 'keepname', 'params': {'sport': 'NBA'}},
        headers=headers,
    )
    sid = json.loads(r.data)['id']

    r = client.put(
        f'/api/saved-searches/{sid}',
        json={'params': {'sport': 'NHL'}},
        headers=headers,
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['name'] == 'keepname'
    assert body['params']['sport'] == 'NHL'


def test_delete_saved_search(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    r = client.post(
        '/api/saved-searches',
        json={'name': 'gone', 'params': {}},
        headers=headers,
    )
    sid = json.loads(r.data)['id']

    r = client.delete(f'/api/saved-searches/{sid}', headers=headers)
    assert r.status_code == 204

    r = client.get(f'/api/saved-searches/{sid}', headers=headers)
    assert r.status_code == 404


def test_user_only_sees_their_own_searches(app_instance):
    with app_instance.app_context():
        a = _make_user('a')
        b = _make_user('b')
        ha = _make_auth_headers(a)
        hb = _make_auth_headers(b)

    ca = app_instance.test_client()
    cb = app_instance.test_client()
    ca.post('/api/saved-searches', json={'name': 's-a', 'params': {}}, headers=ha)
    cb.post('/api/saved-searches', json={'name': 's-b', 'params': {}}, headers=hb)

    ra = ca.get('/api/saved-searches', headers=ha)
    rb = cb.get('/api/saved-searches', headers=hb)
    items_a = json.loads(ra.data)
    items_b = json.loads(rb.data)
    assert len(items_a) == 1 and items_a[0]['name'] == 's-a'
    assert len(items_b) == 1 and items_b[0]['name'] == 's-b'


def test_invalid_params_payload_rejected(client, app_instance):
    with app_instance.app_context():
        user = _make_user()
        headers = _make_auth_headers(user)

    resp = client.post(
        '/api/saved-searches',
        json={'name': 'bad', 'params': 'not-an-object'},
        headers=headers,
    )
    assert resp.status_code == 400
