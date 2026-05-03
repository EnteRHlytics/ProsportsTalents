"""Security headers middleware.

Hand-rolled implementation (no Flask-Talisman dependency) so we keep our
deps small. Sets the following headers on every response:

- ``Content-Security-Policy``       conservative default; can be overridden
                                     via the ``CSP_POLICY`` config key.
- ``X-Frame-Options``               ``DENY``
- ``X-Content-Type-Options``        ``nosniff``
- ``Referrer-Policy``               ``strict-origin-when-cross-origin``
- ``X-XSS-Protection``              ``1; mode=block`` (legacy, but harmless)
- ``Strict-Transport-Security``     only when ``app.config['ENV'] == 'production'``
                                     OR ``HSTS_ENABLED`` is truthy.

Maps to section 4.2 (Security) of the requirements doc.
"""

from __future__ import annotations

from flask import Flask, Response

DEFAULT_CSP = (
    "default-src 'self'; "
    "img-src 'self' data: https:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def _hsts_enabled(app: Flask) -> bool:
    if app.config.get('HSTS_ENABLED'):
        return True
    env = app.config.get('ENV') or ''
    if env.lower() == 'production':
        return True
    # Heuristic: ProductionConfig sets DEBUG=False and SESSION_COOKIE_SECURE=True
    # but we'd rather be explicit. Default off in dev/testing.
    return False


def register_security_headers(app: Flask) -> None:
    """Attach the security-headers ``after_request`` hook to ``app``."""

    csp = app.config.get('CSP_POLICY', DEFAULT_CSP)
    hsts = _hsts_enabled(app)
    hsts_max_age = int(app.config.get('HSTS_MAX_AGE', 31536000))  # 1 year
    hsts_include_subdomains = bool(app.config.get('HSTS_INCLUDE_SUBDOMAINS', True))
    hsts_preload = bool(app.config.get('HSTS_PRELOAD', False))

    @app.after_request
    def _set_security_headers(response: Response) -> Response:
        # Always set baseline headers (idempotent if previously set)
        response.headers['Content-Security-Policy'] = csp
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')

        if hsts:
            value = f'max-age={hsts_max_age}'
            if hsts_include_subdomains:
                value += '; includeSubDomains'
            if hsts_preload:
                value += '; preload'
            response.headers['Strict-Transport-Security'] = value
        return response
