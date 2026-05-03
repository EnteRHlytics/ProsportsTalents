"""Field-level encryption helpers using Fernet (cryptography package).

The encryption key is derived from the application's ``SECRET_KEY`` using
PBKDF2-HMAC-SHA256. The same SECRET_KEY therefore produces the same Fernet
key on every boot, so encrypted columns remain readable across restarts.

Usage
-----
Direct field encryption::

    from app.utils.crypto import encrypt_field, decrypt_field

    cipher = encrypt_field('alice@example.com')
    plain = decrypt_field(cipher)

SQLAlchemy column-level encryption (TypeDecorator)::

    from sqlalchemy import Column, Integer
    from app.utils.crypto import EncryptedString

    class Person(db.Model):
        id = Column(Integer, primary_key=True)
        email_enc = Column(EncryptedString(255))

The ``EncryptedString`` decorator transparently encrypts on write and
decrypts on read. Storage column should be at least roughly
``ceil(len(plain) * 4 / 3) + 100`` bytes to allow for Fernet overhead.

Migration target list (Phase 4 candidate columns)
-------------------------------------------------
The following columns are identified as good candidates for migration to
``EncryptedString``. NOTE: this helper is NOT yet applied to any of these
columns - the agency must confirm each in Phase 4 before we migrate the
schema (column rename + data backfill).

- ``athlete_profiles.contact_email`` (athlete contact email)
- ``athlete_profiles.contact_phone`` (athlete contact phone)
- ``athlete_profiles.emergency_contact_*`` (next-of-kin info, if added)
- ``user_oauth_accounts.access_token`` (already named ``..._encrypted`` but
   currently stores plaintext)
- ``user_oauth_accounts.refresh_token`` (same caveat)

Key rotation
------------
Use ``rotate_key(old_secret, new_secret, ciphertext)`` to re-encrypt a value
when SECRET_KEY is rotated. This module does NOT implement multi-key Fernet
(``MultiFernet``) by default, but it can be added when rotation is needed.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.types import String, TypeDecorator


# Static salt: deliberately fixed so the same SECRET_KEY always produces the
# same Fernet key. Encryption strength comes from SECRET_KEY entropy, not the
# salt. If you need per-column salting, layer it above this helper.
_SALT = b'prosportstalents.v1.fernet'

# PBKDF2 iteration count - tuned for boot-time cost vs. brute-force cost.
_ITERATIONS = 200_000


def _derive_key(secret: str | bytes) -> bytes:
    if isinstance(secret, str):
        secret_bytes = secret.encode('utf-8')
    else:
        secret_bytes = secret
    if not secret_bytes:
        raise ValueError('SECRET_KEY is empty; cannot derive encryption key')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    raw = kdf.derive(secret_bytes)
    return base64.urlsafe_b64encode(raw)


def _get_secret_key() -> str:
    """Resolve the application SECRET_KEY.

    Tries the live Flask ``current_app`` first, falls back to the ``Config``
    class so the helpers also work outside an app context (e.g. scripts).
    """
    try:
        from flask import current_app
        if current_app:
            secret = current_app.config.get('SECRET_KEY')
            if secret:
                return secret
    except Exception:
        pass
    try:
        from config import Config
        secret = Config.SECRET_KEY
        if secret:
            return secret
    except Exception:
        pass
    raise RuntimeError('SECRET_KEY not configured')


def _fernet(secret: Optional[str] = None) -> Fernet:
    secret_value = secret if secret is not None else _get_secret_key()
    key = _derive_key(secret_value)
    return Fernet(key)


def encrypt_field(plaintext: Optional[str], secret: Optional[str] = None) -> Optional[str]:
    """Encrypt ``plaintext`` (str) and return a urlsafe base64 token.

    Returns ``None`` when input is ``None`` so callers don't need to special-case it.
    """
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    token = _fernet(secret).encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_field(ciphertext: Optional[str], secret: Optional[str] = None) -> Optional[str]:
    """Decrypt a token produced by :func:`encrypt_field`.

    Returns ``None`` when input is ``None``. Raises ``InvalidToken`` if the
    ciphertext is corrupted or was encrypted with a different SECRET_KEY.
    """
    if ciphertext is None:
        return None
    if not isinstance(ciphertext, str):
        ciphertext = ciphertext.decode('utf-8') if isinstance(ciphertext, (bytes, bytearray)) else str(ciphertext)
    plain = _fernet(secret).decrypt(ciphertext.encode('utf-8'))
    return plain.decode('utf-8')


def rotate_key(old_secret: str, new_secret: str, ciphertext: str) -> str:
    """Re-encrypt ``ciphertext`` from ``old_secret`` to ``new_secret``."""
    plain = decrypt_field(ciphertext, secret=old_secret)
    return encrypt_field(plain, secret=new_secret)


class EncryptedString(TypeDecorator):
    """SQLAlchemy column type that transparently encrypts strings.

    Stored as ``VARCHAR(length)``. Choose ``length`` generously - Fernet output
    is roughly 1.5x the plaintext length plus ~100 bytes of overhead.

    Reads that fail to decrypt raise ``InvalidToken`` by default. Construct
    with ``swallow_decrypt_errors=True`` to log and return ``None`` instead.
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 512, swallow_decrypt_errors: bool = False, **kwargs):
        self.swallow_decrypt_errors = swallow_decrypt_errors
        super().__init__(length=length, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_field(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return decrypt_field(value)
        except InvalidToken:
            if self.swallow_decrypt_errors:
                # Treat unreadable ciphertext as None; surface in logs.
                try:
                    from flask import current_app
                    if current_app:
                        current_app.logger.warning(
                            'EncryptedString failed to decrypt a column value'
                        )
                except Exception:
                    pass
                return None
            raise


__all__ = [
    'encrypt_field',
    'decrypt_field',
    'rotate_key',
    'EncryptedString',
]
