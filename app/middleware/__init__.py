"""Application-wide WSGI/Flask middleware.

Modules
-------
- ``audit``           after-request hook that records mutating requests in
                       the ``activity_logs`` table.
- ``security_headers``  after-request hook that sets baseline security
                         headers (CSP, HSTS in prod, frame/sniff/referrer).
"""

from .audit import register_audit_middleware
from .security_headers import register_security_headers

__all__ = ['register_audit_middleware', 'register_security_headers']
