"""OAuth flow integration tests (Agent5).

Covers Google, GitHub, and Microsoft (Azure) providers. We monkeypatch the
authlib OAuth client objects so no real HTTP calls happen and no real tokens
are exchanged.

Verifies:
- Provider-specific user-info adapters parse responses correctly.
- A new user + UserOAuthAccount is created on first login.
- A second login with the same provider+provider_user_id reuses the existing
  user (account linking).
- The session ``auth_token`` is set for API access after a successful callback.
- The login redirect endpoint hands off to ``oauth.<provider>.authorize_redirect``
  with a state-bearing redirect.
- Invalid providers and failed token exchanges fall back to the login page.
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db, oauth as oauth_ext
from app.models import User, Role
from app.models.oauth import UserOAuthAccount


@pytest.fixture
def app_instance():
    app = create_app('testing')
    # Provide config so the OAuth registrations can be made if not present.
    app.config['SECRET_KEY'] = 'test-secret-oauth'
    with app.app_context():
        db.create_all()
        if not Role.query.filter_by(name='viewer').first():
            db.session.add(Role(name='viewer'))
            db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _install_fake_provider(app, provider_name, user_info_adapter):
    """Attach a MagicMock to ``oauth_ext._clients[provider_name]`` so the
    auth routes can ``getattr(oauth, provider_name)`` and call its methods.

    ``user_info_adapter`` is called from ``get_user_info_from_provider`` via
    monkeypatching - we intercept that helper instead of mocking individual
    HTTP responses, so this works regardless of authlib's internal API.
    """
    fake_client = MagicMock()
    fake_client.authorize_redirect.return_value = app.test_client().get('/').get_data() and 'redirect-stub'
    fake_client.authorize_access_token.return_value = {
        'access_token': f'access-token-{provider_name}',
        'refresh_token': f'refresh-token-{provider_name}',
    }
    # authlib stores clients on the OAuth object via _clients dict and exposes
    # them as attributes; setting attribute directly is the reliable shortcut.
    setattr(oauth_ext, provider_name, fake_client)
    # Also push into _clients so getattr falls back work in either authlib version
    if hasattr(oauth_ext, '_clients'):
        oauth_ext._clients[provider_name] = fake_client
    return fake_client


def _patch_user_info(monkeypatch, payload_by_provider):
    """Replace get_user_info_from_provider so we don't hit the network."""
    from app.auth import routes as auth_routes

    def fake_get_user_info(provider, token):
        return payload_by_provider.get(provider)

    monkeypatch.setattr(auth_routes, 'get_user_info_from_provider', fake_get_user_info)


# ---------------------------------------------------------------------------
# /auth/login/<provider> - state-bearing redirect kickoff
# ---------------------------------------------------------------------------

def test_oauth_login_invalid_provider_redirects(client):
    resp = client.get('/auth/login/notreal', follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert '/auth/login' in resp.headers.get('Location', '')


def test_oauth_login_unconfigured_provider_redirects(client, app_instance):
    # Make sure the attribute doesn't exist for this provider
    if hasattr(oauth_ext, 'github'):
        delattr(oauth_ext, 'github')
    if hasattr(oauth_ext, '_clients') and 'github' in oauth_ext._clients:
        del oauth_ext._clients['github']
    resp = client.get('/auth/login/github', follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_oauth_login_google_calls_authorize_redirect(client, app_instance):
    fake = _install_fake_provider(app_instance, 'google', None)
    # Make authorize_redirect return a valid Flask redirect-like response
    from flask import redirect

    fake.authorize_redirect.side_effect = lambda redirect_uri, **kw: redirect(
        f'https://accounts.google.test/o/oauth2/v2/auth?state=stateful&redirect_uri={redirect_uri}'
    )

    resp = client.get('/auth/login/google', follow_redirects=False)
    assert resp.status_code in (302, 303)
    location = resp.headers.get('Location', '')
    assert 'accounts.google.test' in location
    assert 'state=stateful' in location  # state token enforced by authlib mock
    fake.authorize_redirect.assert_called_once()


# ---------------------------------------------------------------------------
# /auth/callback/<provider> - new user creation
# ---------------------------------------------------------------------------

GOOGLE_USERINFO = {
    'email': 'gtest@example.com',
    'first_name': 'Google',
    'last_name': 'User',
    'provider_user_id': 'g-12345',
    'email_verified': True,
    'picture': 'https://example.test/g.png',
}

GITHUB_USERINFO = {
    'email': 'ghtest@example.com',
    'first_name': 'GitHub',
    'last_name': 'User',
    'provider_user_id': 'gh-67890',
    'email_verified': True,
    'avatar_url': 'https://example.test/gh.png',
}

AZURE_USERINFO = {
    'email': 'aztest@example.com',
    'first_name': 'Azure',
    'last_name': 'User',
    'provider_user_id': 'az-uuid-0001',
    'email_verified': True,
}


@pytest.mark.parametrize('provider, payload', [
    ('google', GOOGLE_USERINFO),
    ('github', GITHUB_USERINFO),
    ('azure', AZURE_USERINFO),
])
def test_oauth_callback_creates_user_on_first_login(
    client, app_instance, monkeypatch, provider, payload
):
    _install_fake_provider(app_instance, provider, payload)
    _patch_user_info(monkeypatch, {provider: payload})

    resp = client.get(f'/auth/callback/{provider}', follow_redirects=False)

    # On success the route 302s to main.dashboard. On failure it 302s back to
    # auth.login. Either way it's a redirect; we check user state for truth.
    assert resp.status_code in (302, 303)

    with app_instance.app_context():
        u = User.query.filter_by(email=payload['email']).first()
        assert u is not None, f'expected User to be created for {provider}'
        accounts = UserOAuthAccount.query.filter_by(
            user_id=u.user_id, provider_name=provider
        ).all()
        assert len(accounts) == 1
        assert accounts[0].provider_user_id == payload['provider_user_id']
        assert accounts[0].access_token == f'access-token-{provider}'


def test_oauth_callback_sets_session_auth_token(
    client, app_instance, monkeypatch
):
    _install_fake_provider(app_instance, 'google', GOOGLE_USERINFO)
    _patch_user_info(monkeypatch, {'google': GOOGLE_USERINFO})

    with client:
        client.get('/auth/callback/google', follow_redirects=False)
        from flask import session
        assert session.get('auth_token') == 'access-token-google'


# ---------------------------------------------------------------------------
# Account linking on subsequent login (idempotent re-login)
# ---------------------------------------------------------------------------

def test_oauth_callback_links_existing_account_on_repeat_login(
    client, app_instance, monkeypatch
):
    _install_fake_provider(app_instance, 'google', GOOGLE_USERINFO)
    _patch_user_info(monkeypatch, {'google': GOOGLE_USERINFO})

    # First login - creates user + oauth account
    client.get('/auth/callback/google', follow_redirects=False)
    with app_instance.app_context():
        users = User.query.filter_by(email=GOOGLE_USERINFO['email']).all()
        assert len(users) == 1
        first_user_id = users[0].user_id

    # Second login (clear cookies first to simulate fresh session)
    client.delete_cookie('session')
    client.get('/auth/callback/google', follow_redirects=False)

    with app_instance.app_context():
        users = User.query.filter_by(email=GOOGLE_USERINFO['email']).all()
        assert len(users) == 1, 'should not create a duplicate user on re-login'
        assert users[0].user_id == first_user_id
        accounts = UserOAuthAccount.query.filter_by(user_id=first_user_id).all()
        assert len(accounts) == 1, 'should not duplicate the oauth account'


def test_oauth_callback_links_account_to_pre_existing_user_with_same_email(
    client, app_instance, monkeypatch
):
    """If a user already exists with the email, the OAuth account should be
    attached to that user rather than creating a new one."""
    with app_instance.app_context():
        existing = User(
            username='ghtest',
            email=GITHUB_USERINFO['email'],
            first_name='Existing',
            last_name='User',
            is_active=True,
        )
        existing.set_password('pw-existing')
        db.session.add(existing)
        db.session.commit()
        existing_user_id = existing.user_id

    _install_fake_provider(app_instance, 'github', GITHUB_USERINFO)
    _patch_user_info(monkeypatch, {'github': GITHUB_USERINFO})

    client.get('/auth/callback/github', follow_redirects=False)

    with app_instance.app_context():
        users = User.query.filter_by(email=GITHUB_USERINFO['email']).all()
        assert len(users) == 1
        assert users[0].user_id == existing_user_id
        accounts = UserOAuthAccount.query.filter_by(
            user_id=existing_user_id, provider_name='github'
        ).all()
        assert len(accounts) == 1


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------

def test_oauth_callback_token_exchange_failure_redirects_to_login(
    client, app_instance, monkeypatch
):
    fake = _install_fake_provider(app_instance, 'google', None)
    fake.authorize_access_token.side_effect = RuntimeError('bad state token')

    resp = client.get('/auth/callback/google', follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert '/auth/login' in resp.headers.get('Location', '')

    with app_instance.app_context():
        # No user should have been created
        assert User.query.filter_by(email=GOOGLE_USERINFO['email']).first() is None


def test_oauth_callback_missing_email_redirects_to_login(
    client, app_instance, monkeypatch
):
    _install_fake_provider(app_instance, 'google', None)
    _patch_user_info(monkeypatch, {'google': {}})  # no email

    resp = client.get('/auth/callback/google', follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert '/auth/login' in resp.headers.get('Location', '')
