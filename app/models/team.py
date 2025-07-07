from app import db
from app.models.base import BaseModel


class Team(BaseModel):
    """Generic team table supporting multiple sports."""

    __tablename__ = 'teams'

    team_id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.sport_id'), nullable=False
    )
    abbreviation = db.Column(db.String(10))
    city = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    league = db.Column(db.String(50))

    sport = db.relationship('Sport')
    games_home = db.relationship(
        'Game', back_populates='home_team', foreign_keys='Game.home_team_id'
    )
    games_away = db.relationship(
        'Game', back_populates='visitor_team', foreign_keys='Game.visitor_team_id'
    )

    def __repr__(self):
        return f'<Team {self.name}>'

class NBATeam(BaseModel):
    __tablename__ = 'nba_teams'

    team_id = db.Column(db.Integer, primary_key=True)
    abbreviation = db.Column(db.String(10))
    city = db.Column(db.String(50))
    conference = db.Column(db.String(20))
    division = db.Column(db.String(50))
    full_name = db.Column(db.String(100))
    name = db.Column(db.String(100))

    games_home = db.relationship('NBAGame', back_populates='home_team', foreign_keys='NBAGame.home_team_id')
    games_away = db.relationship('NBAGame', back_populates='visitor_team', foreign_keys='NBAGame.visitor_team_id')

    def __repr__(self):
        return f'<NBATeam {self.full_name}>'


class MLBTeam(BaseModel):
    __tablename__ = 'mlb_teams'

    team_id = db.Column(db.Integer, primary_key=True)
    abbreviation = db.Column(db.String(10))
    name = db.Column(db.String(100))
    location = db.Column(db.String(50))
    league = db.Column(db.String(50))
    division = db.Column(db.String(50))

    def __repr__(self):
        return f'<MLBTeam {self.name}>'


class NFLTeam(BaseModel):
    __tablename__ = 'nfl_teams'

    team_id = db.Column(db.Integer, primary_key=True)
    abbreviation = db.Column(db.String(10))
    city = db.Column(db.String(50))
    conference = db.Column(db.String(50))
    division = db.Column(db.String(50))
    name = db.Column(db.String(100))

    def __repr__(self):
        return f'<NFLTeam {self.name}>'


class NHLTeam(BaseModel):
    __tablename__ = 'nhl_teams'

    team_id = db.Column(db.Integer, primary_key=True)
    abbreviation = db.Column(db.String(10))
    name = db.Column(db.String(100))
    location = db.Column(db.String(50))
    conference = db.Column(db.String(50))
    division = db.Column(db.String(50))
    wins = db.Column(db.Integer)
    losses = db.Column(db.Integer)
    overtime_losses = db.Column(db.Integer)
    points = db.Column(db.Integer)

    games_home = db.relationship('NHLGame', back_populates='home_team', foreign_keys='NHLGame.home_team_id')
    games_away = db.relationship('NHLGame', back_populates='visitor_team', foreign_keys='NHLGame.visitor_team_id')

    def __repr__(self):
        return f'<NHLTeam {self.name}>'
