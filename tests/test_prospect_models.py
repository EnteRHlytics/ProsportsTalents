"""Model-level tests for prospect & api_key schemas."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import (
    ApiKey,
    MinorLeagueTeam,
    Prospect,
    ProspectLeague,
    ProspectStat,
    User,
)

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _make_league(code='NCAA_BB_D1', name='NCAA D1 Basketball'):
    league = ProspectLeague(code=code, name=name, is_pro_pipeline=True, country='USA')
    db.session.add(league)
    db.session.commit()
    return league


def _make_prospect(**overrides):
    defaults = dict(
        first_name='Sample',
        last_name='Prospect',
        date_of_birth=date(2003, 1, 15),
        height_cm=193,
        weight_kg=88.5,
        scout_grade=72,
    )
    defaults.update(overrides)
    prospect = Prospect(**defaults)
    db.session.add(prospect)
    db.session.commit()
    return prospect


def test_prospect_uuid_pk_generated(app_instance):
    p = _make_prospect()
    assert p.prospect_id is not None
    assert UUID_RE.match(p.prospect_id), p.prospect_id


def test_prospect_league_uuid_pk_generated(app_instance):
    league = _make_league()
    assert UUID_RE.match(league.prospect_league_id)


def test_prospect_league_code_unique(app_instance):
    _make_league(code='NCAA_BB_D1')
    db.session.add(ProspectLeague(code='NCAA_BB_D1', name='dup'))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_minor_league_team_external_id_unique_per_league(app_instance):
    league = _make_league()
    a = MinorLeagueTeam(
        prospect_league_id=league.prospect_league_id,
        name='Team A',
        external_id='ext-1',
    )
    db.session.add(a)
    db.session.commit()

    dup = MinorLeagueTeam(
        prospect_league_id=league.prospect_league_id,
        name='Team A duplicate',
        external_id='ext-1',
    )
    db.session.add(dup)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_prospect_stat_unique_per_season_and_name(app_instance):
    p = _make_prospect()
    db.session.add(
        ProspectStat(
            prospect_id=p.prospect_id, season='2025', name='PPG', value='18.4'
        )
    )
    db.session.commit()
    dup = ProspectStat(
        prospect_id=p.prospect_id, season='2025', name='PPG', value='17.0'
    )
    db.session.add(dup)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_prospect_stat_same_name_different_season_ok(app_instance):
    p = _make_prospect()
    db.session.add_all([
        ProspectStat(prospect_id=p.prospect_id, season='2024', name='PPG', value='15.0'),
        ProspectStat(prospect_id=p.prospect_id, season='2025', name='PPG', value='18.0'),
    ])
    db.session.commit()
    rows = ProspectStat.query.filter_by(prospect_id=p.prospect_id, name='PPG').all()
    assert len(rows) == 2


def test_prospect_soft_delete_query_filter(app_instance):
    p = _make_prospect()
    pid = p.prospect_id

    # Soft-delete
    p.is_deleted = True
    db.session.commit()

    # Filtered query excludes soft-deleted
    visible = Prospect.query.filter_by(is_deleted=False).all()
    assert all(row.prospect_id != pid for row in visible)

    # Direct lookup still finds the row (audit recovery)
    row = Prospect.query.filter_by(prospect_id=pid).first()
    assert row is not None
    assert row.is_deleted is True


def test_prospect_to_dict_serialises_expected_fields(app_instance):
    p = _make_prospect(weight_kg=90)
    data = p.to_dict()
    assert data['prospect_id'] == p.prospect_id
    assert data['full_name'] == 'Sample Prospect'
    assert data['height_cm'] == 193
    assert isinstance(data['weight_kg'], float)
    assert data['is_deleted'] is False
    assert 'created_at' in data
    assert 'age' in data


def test_apikey_generate_returns_raw_and_only_stores_hash(app_instance):
    user = User(username='kuser', email='k@example.com', first_name='K', last_name='U')
    user.save()

    record, raw = ApiKey.generate(user_id=user.user_id, name='primary')
    db.session.add(record)
    db.session.commit()

    # raw key is non-empty and not stored verbatim
    assert isinstance(raw, str) and len(raw) >= 32
    assert record.key_hash != raw
    assert ApiKey.query.filter_by(key_hash=raw).first() is None

    # but lookup by raw key works
    looked_up = ApiKey.find_by_raw_key(raw)
    assert looked_up is not None
    assert looked_up.api_key_id == record.api_key_id


def test_apikey_find_by_raw_key_respects_active_and_expiry(app_instance):
    user = User(username='kuser2', email='k2@example.com', first_name='K', last_name='U')
    user.save()

    record, raw = ApiKey.generate(user_id=user.user_id, name='temp')
    db.session.add(record)
    db.session.commit()

    record.is_active = False
    db.session.commit()
    assert ApiKey.find_by_raw_key(raw) is None

    record.is_active = True
    record.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.session.commit()
    assert ApiKey.find_by_raw_key(raw) is None


def test_apikey_to_dict_does_not_leak_hash(app_instance):
    user = User(username='kuser3', email='k3@example.com', first_name='K', last_name='U')
    user.save()
    record, _ = ApiKey.generate(user_id=user.user_id, name='disp')
    db.session.add(record)
    db.session.commit()

    data = record.to_dict()
    assert 'key_hash' not in data
    assert 'key' not in data
    assert data['key_prefix'] == record.key_prefix


def test_prospect_height_check_constraint(app_instance):
    bad = Prospect(first_name='Bad', last_name='Height', height_cm=50)
    db.session.add(bad)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
