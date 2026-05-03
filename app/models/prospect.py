"""Prospect scouting models.

A ``Prospect`` is a pre-pro athlete the agency is scouting (high school,
college, G-League, MiLB, etc.) who has NOT yet signed a pro contract.
This is distinct from ``AthleteProfile`` which tracks signed pros.

Wave-1 supplied minimal stub schemas so the application could boot. This
module replaces those stubs with the real production schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app import db
from app.models.base import BaseModel


class ProspectLeague(BaseModel):
    """A pre-pro league: NCAA, G-League, MiLB AAA/AA/A, etc."""

    __tablename__ = 'prospect_leagues'

    prospect_league_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code = db.Column(db.String(40), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.sport_id'), nullable=True, index=True
    )
    is_pro_pipeline = db.Column(db.Boolean, default=True, nullable=False)
    country = db.Column(db.String(3))  # ISO 3166-1 alpha-3

    sport = db.relationship('Sport')
    teams = db.relationship(
        'MinorLeagueTeam', back_populates='league', cascade='all, delete-orphan'
    )

    def to_dict(self) -> dict:
        return {
            'prospect_league_id': self.prospect_league_id,
            'code': self.code,
            'name': self.name,
            'sport_id': self.sport_id,
            'is_pro_pipeline': bool(self.is_pro_pipeline),
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f'<ProspectLeague {self.code}>'


class MinorLeagueTeam(BaseModel):
    """A team that competes in a ``ProspectLeague``."""

    __tablename__ = 'minor_league_teams'

    team_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    prospect_league_id = db.Column(
        db.String(36),
        db.ForeignKey('prospect_leagues.prospect_league_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    abbreviation = db.Column(db.String(10))
    city = db.Column(db.String(100))
    external_id = db.Column(db.String(64), index=True)

    league = db.relationship('ProspectLeague', back_populates='teams')
    prospects = db.relationship(
        'Prospect',
        back_populates='current_team',
        foreign_keys='Prospect.current_team_id',
    )

    __table_args__ = (
        db.UniqueConstraint(
            'prospect_league_id',
            'external_id',
            name='uq_minor_league_team_league_external',
        ),
    )

    def to_dict(self) -> dict:
        return {
            'team_id': self.team_id,
            'prospect_league_id': self.prospect_league_id,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'city': self.city,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f'<MinorLeagueTeam {self.name}>'


class Prospect(BaseModel):
    """A pre-pro athlete the agency is scouting."""

    __tablename__ = 'prospects'

    prospect_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Numeric(5, 2))

    primary_sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.sport_id'), nullable=True, index=True
    )
    primary_position_id = db.Column(
        db.Integer, db.ForeignKey('positions.position_id'), nullable=True
    )
    current_team_id = db.Column(
        db.String(36),
        db.ForeignKey('minor_league_teams.team_id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    prospect_league_id = db.Column(
        db.String(36),
        db.ForeignKey('prospect_leagues.prospect_league_id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    school = db.Column(db.String(150))
    draft_eligible_year = db.Column(db.Integer, index=True)
    scout_grade = db.Column(db.Integer)  # 0-100
    scout_notes = db.Column(db.Text)
    bio = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    external_id = db.Column(db.String(64), index=True)

    primary_sport = db.relationship('Sport')
    primary_position = db.relationship('Position')
    current_team = db.relationship(
        'MinorLeagueTeam',
        back_populates='prospects',
        foreign_keys=[current_team_id],
    )
    league = db.relationship('ProspectLeague', foreign_keys=[prospect_league_id])
    stats = db.relationship(
        'ProspectStat', back_populates='prospect', cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.CheckConstraint(
            'height_cm IS NULL OR (height_cm BETWEEN 100 AND 250)',
            name='ck_prospect_height_reasonable',
        ),
        db.CheckConstraint(
            'weight_kg IS NULL OR (weight_kg BETWEEN 30 AND 200)',
            name='ck_prospect_weight_reasonable',
        ),
        db.CheckConstraint(
            'scout_grade IS NULL OR (scout_grade BETWEEN 0 AND 100)',
            name='ck_prospect_scout_grade_range',
        ),
        db.Index('idx_prospects_name', 'last_name', 'first_name'),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day)
            < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self, include_stats: bool = False) -> dict:
        data = {
            'prospect_id': self.prospect_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': (
                self.date_of_birth.isoformat() if self.date_of_birth else None
            ),
            'age': self.age,
            'height_cm': self.height_cm,
            'weight_kg': float(self.weight_kg) if self.weight_kg is not None else None,
            'primary_sport_id': self.primary_sport_id,
            'primary_position_id': self.primary_position_id,
            'current_team_id': self.current_team_id,
            'prospect_league_id': self.prospect_league_id,
            'school': self.school,
            'draft_eligible_year': self.draft_eligible_year,
            'scout_grade': self.scout_grade,
            'scout_notes': self.scout_notes,
            'bio': self.bio,
            'is_deleted': bool(self.is_deleted),
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_stats:
            data['stats'] = [s.to_dict() for s in self.stats]
        return data

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f'<Prospect {self.full_name}>'


class ProspectStat(BaseModel):
    """A single named statistic for a prospect, in a specific season."""

    __tablename__ = 'prospect_stats'

    prospect_stat_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    prospect_id = db.Column(
        db.String(36),
        db.ForeignKey('prospects.prospect_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    season = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.String(120))
    stat_type = db.Column(db.String(40))
    source = db.Column(db.String(80))

    prospect = db.relationship('Prospect', back_populates='stats')

    __table_args__ = (
        db.UniqueConstraint(
            'prospect_id', 'season', 'name', name='uq_prospect_stat_season_name'
        ),
        db.Index('idx_prospect_stat_prospect_season', 'prospect_id', 'season'),
    )

    def to_dict(self) -> dict:
        return {
            'prospect_stat_id': self.prospect_stat_id,
            'prospect_id': self.prospect_id,
            'season': self.season,
            'name': self.name,
            'value': self.value,
            'stat_type': self.stat_type,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f'<ProspectStat {self.prospect_id} {self.season} {self.name}>'
