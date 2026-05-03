"""Prospect model stubs.

NOTE (Agent5): ``app/models/__init__.py`` imports these names; the full
implementations belong to the prospects agent. The classes here are minimal
SQLAlchemy models so the application can boot and unrelated tests can run.
They should be overwritten by the owning agent's real implementation.
"""

from datetime import datetime
import uuid

from app import db


class ProspectLeague(db.Model):
    __tablename__ = 'prospect_leagues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    sport = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MinorLeagueTeam(db.Model):
    __tablename__ = 'minor_league_teams'

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('prospect_leagues.id'))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    parent_team = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prospect(db.Model):
    __tablename__ = 'prospects'

    prospect_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    league_id = db.Column(db.Integer, db.ForeignKey('prospect_leagues.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('minor_league_teams.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProspectStat(db.Model):
    __tablename__ = 'prospect_stats'

    id = db.Column(db.Integer, primary_key=True)
    prospect_id = db.Column(db.String(36), db.ForeignKey('prospects.prospect_id'))
    name = db.Column(db.String(100))
    value = db.Column(db.String(100))
    season = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
