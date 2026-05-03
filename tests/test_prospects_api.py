"""HTTP-level tests for /api/prospects endpoints."""

from __future__ import annotations

import json
from datetime import date

import pytest

from app import create_app, db
from app.models import (
    MinorLeagueTeam,
    Prospect,
    ProspectLeague,
    ProspectStat,
    Sport,
    User,
)
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


@pytest.fixture
def auth_headers(app_instance):
    with app_instance.app_context():
        user = User(
            username='prospect_writer',
            email='pw@example.com',
            first_name='P',
            last_name='W',
        )
        user.save()
        oauth = UserOAuthAccount(
            user_id=user.user_id,
            provider_name='test',
            provider_user_id='1',
            access_token='prospect-token',
        )
        db.session.add(oauth)
        db.session.commit()
    return {'Authorization': 'Bearer prospect-token'}


def _create_prospect(**overrides):
    defaults = dict(
        first_name='Jordan',
        last_name='Smith',
        date_of_birth=date(2003, 4, 1),
        scout_grade=72,
    )
    defaults.update(overrides)
    p = Prospect(**defaults)
    db.session.add(p)
    db.session.commit()
    return p


# ----- list/search ---------------------------------------------------------

def test_list_prospects_returns_paginated_payload(client, app_instance):
    with app_instance.app_context():
        for i in range(3):
            _create_prospect(first_name=f'F{i}', last_name=f'L{i}')

    resp = client.get('/api/prospects')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['total'] == 3
    assert len(body['items']) == 3
    assert body['page'] == 1


def test_list_prospects_supports_q_search(client, app_instance):
    with app_instance.app_context():
        _create_prospect(first_name='Aaron', last_name='Hill')
        _create_prospect(first_name='Brad', last_name='Jones')

    resp = client.get('/api/prospects?q=Aaron')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['total'] == 1
    assert body['items'][0]['first_name'] == 'Aaron'


def test_list_prospects_filters_by_league_code(client, app_instance):
    with app_instance.app_context():
        league = ProspectLeague(code='NCAA_BB_D1', name='NCAA D1 BB')
        db.session.add(league)
        db.session.commit()
        _create_prospect(prospect_league_id=league.prospect_league_id)
        _create_prospect()  # no league

    resp = client.get('/api/prospects?league=NCAA_BB_D1')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['total'] == 1


def test_list_prospects_filters_by_draft_year(client, app_instance):
    with app_instance.app_context():
        _create_prospect(draft_eligible_year=2026)
        _create_prospect(draft_eligible_year=2027)

    resp = client.get('/api/prospects?draft_year=2026')
    body = resp.get_json()
    assert resp.status_code == 200
    assert body['total'] == 1
    assert body['items'][0]['draft_eligible_year'] == 2026


def test_list_prospects_filters_by_sport_code(client, app_instance):
    with app_instance.app_context():
        sport = Sport(name='Basketball', code='NBA')
        db.session.add(sport)
        db.session.commit()
        _create_prospect(primary_sport_id=sport.sport_id)
        _create_prospect()  # no sport

    resp = client.get('/api/prospects?sport=NBA')
    body = resp.get_json()
    assert resp.status_code == 200
    assert body['total'] == 1


# ----- create / detail / update / delete ----------------------------------

def test_create_prospect_requires_auth(client):
    resp = client.post(
        '/api/prospects',
        json={'first_name': 'New', 'last_name': 'Guy'},
    )
    assert resp.status_code == 401


def test_create_prospect_validates_required_fields(client, auth_headers):
    resp = client.post('/api/prospects', json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_create_and_get_prospect(client, auth_headers, app_instance):
    payload = {
        'first_name': 'Cole',
        'last_name': 'Walker',
        'date_of_birth': '2004-09-12',
        'scout_grade': 81,
        'school': 'State University',
    }
    resp = client.post('/api/prospects', json=payload, headers=auth_headers)
    assert resp.status_code == 201
    created = resp.get_json()
    assert created['first_name'] == 'Cole'
    assert created['scout_grade'] == 81

    detail = client.get(f"/api/prospects/{created['prospect_id']}")
    assert detail.status_code == 200
    assert detail.get_json()['school'] == 'State University'


def test_create_prospect_rejects_invalid_grade(client, auth_headers):
    resp = client.post(
        '/api/prospects',
        json={'first_name': 'A', 'last_name': 'B', 'scout_grade': 200},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_update_prospect(client, auth_headers, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id

    resp = client.put(
        f'/api/prospects/{pid}',
        json={'school': 'New School', 'scout_grade': 90},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['school'] == 'New School'
    assert body['scout_grade'] == 90


def test_update_prospect_requires_auth(client, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id
    resp = client.put(f'/api/prospects/{pid}', json={'school': 'X'})
    assert resp.status_code == 401


def test_soft_delete_prospect(client, auth_headers, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id

    resp = client.delete(f'/api/prospects/{pid}', headers=auth_headers)
    assert resp.status_code == 204

    # The detail endpoint hides soft-deleted prospects
    again = client.get(f'/api/prospects/{pid}')
    assert again.status_code == 404

    # The list does too
    listed = client.get('/api/prospects')
    assert listed.get_json()['total'] == 0


def test_delete_prospect_requires_auth(client, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id
    resp = client.delete(f'/api/prospects/{pid}')
    assert resp.status_code == 401


def test_get_unknown_prospect_returns_404(client):
    resp = client.get('/api/prospects/does-not-exist')
    assert resp.status_code == 404


# ----- prospect stats ------------------------------------------------------

def test_list_prospect_stats(client, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        db.session.add_all([
            ProspectStat(prospect_id=p.prospect_id, season='2025', name='PPG', value='18.5'),
            ProspectStat(prospect_id=p.prospect_id, season='2024', name='PPG', value='14.2'),
        ])
        db.session.commit()
        pid = p.prospect_id

    resp = client.get(f'/api/prospects/{pid}/stats')
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 2

    filtered = client.get(f'/api/prospects/{pid}/stats?season=2025')
    assert filtered.status_code == 200
    rows = filtered.get_json()
    assert len(rows) == 1
    assert rows[0]['value'] == '18.5'


def test_upsert_prospect_stat_creates_then_updates(
    client, auth_headers, app_instance
):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id

    payload = {'season': '2025', 'name': 'PPG', 'value': '18.0', 'stat_type': 'avg'}
    create_resp = client.post(
        f'/api/prospects/{pid}/stats', json=payload, headers=auth_headers
    )
    assert create_resp.status_code == 201
    created = create_resp.get_json()
    assert created['value'] == '18.0'

    update_resp = client.post(
        f'/api/prospects/{pid}/stats',
        json={'season': '2025', 'name': 'PPG', 'value': '20.4'},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert updated['value'] == '20.4'

    with app_instance.app_context():
        rows = ProspectStat.query.filter_by(prospect_id=pid, name='PPG').all()
        assert len(rows) == 1
        assert rows[0].value == '20.4'


def test_upsert_prospect_stat_requires_auth(client, app_instance):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id
    resp = client.post(
        f'/api/prospects/{pid}/stats',
        json={'season': '2025', 'name': 'PPG', 'value': '12'},
    )
    assert resp.status_code == 401


def test_upsert_prospect_stat_validates_required_fields(
    client, auth_headers, app_instance
):
    with app_instance.app_context():
        p = _create_prospect()
        pid = p.prospect_id
    resp = client.post(
        f'/api/prospects/{pid}/stats', json={'season': '2025'}, headers=auth_headers
    )
    assert resp.status_code == 400
