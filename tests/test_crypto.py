"""Tests for app.utils.crypto encryption helpers and EncryptedString (Agent5)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography.fernet import InvalidToken
from sqlalchemy import Column, Integer

from app import create_app, db
from app.utils.crypto import (
    EncryptedString,
    decrypt_field,
    encrypt_field,
    rotate_key,
)


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ---------------------------------------------------------------------------
# encrypt_field / decrypt_field
# ---------------------------------------------------------------------------

def test_roundtrip_basic(app_instance):
    plain = 'sensitive@example.com'
    cipher = encrypt_field(plain)
    assert cipher != plain
    assert decrypt_field(cipher) == plain


def test_roundtrip_unicode(app_instance):
    plain = 'naïve résumé 日本語'
    cipher = encrypt_field(plain)
    assert decrypt_field(cipher) == plain


def test_none_passthrough(app_instance):
    assert encrypt_field(None) is None
    assert decrypt_field(None) is None


def test_empty_string_roundtrip(app_instance):
    cipher = encrypt_field('')
    assert decrypt_field(cipher) == ''


def test_distinct_ciphertexts_for_same_plain(app_instance):
    # Fernet uses a random IV, so the same plaintext should produce
    # different ciphertexts
    a = encrypt_field('hello')
    b = encrypt_field('hello')
    assert a != b
    assert decrypt_field(a) == 'hello'
    assert decrypt_field(b) == 'hello'


def test_decrypt_with_wrong_secret_raises(app_instance):
    cipher = encrypt_field('secret value', secret='key-A')
    with pytest.raises(InvalidToken):
        decrypt_field(cipher, secret='key-B')


def test_rotate_key_roundtrip(app_instance):
    plain = 'rotation test'
    a = encrypt_field(plain, secret='old-key')
    b = rotate_key('old-key', 'new-key', a)
    assert decrypt_field(b, secret='new-key') == plain
    # Old token still readable with old key
    assert decrypt_field(a, secret='old-key') == plain


def test_secret_required(monkeypatch, app_instance):
    monkeypatch.setattr('app.utils.crypto._get_secret_key', lambda: '')
    with pytest.raises(ValueError):
        encrypt_field('x')


# ---------------------------------------------------------------------------
# EncryptedString TypeDecorator
# ---------------------------------------------------------------------------

def _build_secret_model():
    """Build a fresh model class on a fresh metadata to avoid table-name clashes
    between test runs/imports."""
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class SecretRow(Base):
        __tablename__ = 'crypto_secret_rows'
        id = Column(Integer, primary_key=True)
        value_enc = Column(EncryptedString(1024))

    return Base, SecretRow


def test_encrypted_string_roundtrip(app_instance):
    Base, SecretRow = _build_secret_model()
    engine = db.engine
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import Session
    with Session(engine) as session:
        row = SecretRow(value_enc='alice@example.com')
        session.add(row)
        session.commit()
        rid = row.id
        # Read back via fresh session-scoped query to avoid identity-map cache
        session.expire_all()
        fetched = session.get(SecretRow, rid)
        assert fetched.value_enc == 'alice@example.com'

    # Confirm the raw row in the DB is NOT plaintext
    from sqlalchemy import text
    with engine.connect() as conn:
        raw = conn.execute(
            text('SELECT value_enc FROM crypto_secret_rows WHERE id = :i'),
            {'i': rid},
        ).scalar()
        assert raw is not None
        assert 'alice@example.com' not in raw

    Base.metadata.drop_all(engine)


def test_encrypted_string_handles_none(app_instance):
    Base, SecretRow = _build_secret_model()
    engine = db.engine
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import Session
    with Session(engine) as session:
        row = SecretRow(value_enc=None)
        session.add(row)
        session.commit()
        rid = row.id
        session.expire_all()
        fetched = session.get(SecretRow, rid)
        assert fetched.value_enc is None

    Base.metadata.drop_all(engine)


def test_encrypted_string_swallow_decrypt_errors(app_instance):
    """When swallow_decrypt_errors=True, garbage ciphertext returns None."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session, declarative_base

    Base = declarative_base()

    class TolerantRow(Base):
        __tablename__ = 'crypto_tolerant_rows'
        id = Column(Integer, primary_key=True)
        value_enc = Column(EncryptedString(1024, swallow_decrypt_errors=True))

    engine = db.engine
    Base.metadata.create_all(engine)

    # Insert garbage straight into the column
    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO crypto_tolerant_rows (id, value_enc) VALUES (1, :v)'),
            {'v': 'not-a-real-fernet-token'},
        )

    with Session(engine) as session:
        fetched = session.get(TolerantRow, 1)
        assert fetched.value_enc is None

    Base.metadata.drop_all(engine)
