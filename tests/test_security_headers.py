"""Tests for security headers middleware (Agent5)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.middleware.security_headers import DEFAULT_CSP


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_x_frame_options_deny(client):
    resp = client.get('/auth/login')
    assert resp.headers.get('X-Frame-Options') == 'DENY'


def test_x_content_type_options_nosniff(client):
    resp = client.get('/auth/login')
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'


def test_referrer_policy(client):
    resp = client.get('/auth/login')
    assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'


def test_csp_present(client):
    resp = client.get('/auth/login')
    csp = resp.headers.get('Content-Security-Policy')
    assert csp
    # Sanity: includes some essential directives
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_csp_default_constant_used(client):
    # Pure unit-style check - the middleware uses DEFAULT_CSP unless overridden
    resp = client.get('/auth/login')
    csp = resp.headers.get('Content-Security-Policy')
    assert csp == DEFAULT_CSP


def test_hsts_disabled_in_testing(client):
    # Testing config should NOT emit HSTS (only prod).
    resp = client.get('/auth/login')
    assert 'Strict-Transport-Security' not in resp.headers


def test_hsts_enabled_when_configured():
    """HSTS_ENABLED forces the header on regardless of env."""
    app = create_app('testing')
    app.config['HSTS_ENABLED'] = True
    # Re-register middleware so the new flag is picked up.
    from app.middleware.security_headers import register_security_headers
    register_security_headers(app)

    with app.app_context():
        db.create_all()
        try:
            client = app.test_client()
            resp = client.get('/auth/login')
            hsts = resp.headers.get('Strict-Transport-Security')
            assert hsts is not None
            assert 'max-age=' in hsts
            assert 'includeSubDomains' in hsts
        finally:
            db.session.remove()
            db.drop_all()


def test_security_headers_set_on_post(client):
    # Make sure mutating requests also get the security headers
    resp = client.post(
        '/auth/login', data={'username_or_email': 'x', 'password': 'x'}
    )
    assert resp.headers.get('X-Frame-Options') == 'DENY'
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
