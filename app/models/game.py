from app import db
from app.models.base import BaseModel


class Game(BaseModel):
    """Generic game table supporting multiple sports."""

    __tablename__ = 'games'

    game_id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.sport_id'), nullable=False
    )
    season = db.Column(db.String(10))
    date = db.Column(db.Date)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'))
    visitor_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'))
    home_team_score = db.Column(db.Integer)
    visitor_team_score = db.Column(db.Integer)

    sport = db.relationship('Sport')
    home_team = db.relationship('Team', foreign_keys=[home_team_id], back_populates='games_home')
    visitor_team = db.relationship('Team', foreign_keys=[visitor_team_id], back_populates='games_away')

    __table_args__ = (
        db.CheckConstraint('home_team_score >= 0', name='ck_game_home_score_non_negative'),
        db.CheckConstraint('visitor_team_score >= 0', name='ck_game_visitor_score_non_negative'),
    )

    def __repr__(self):
        return f'<Game {self.game_id}>'

class NBAGame(BaseModel):
    __tablename__ = 'nba_games'

    game_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    season = db.Column(db.Integer)
    home_team_id = db.Column(db.Integer, db.ForeignKey('nba_teams.team_id'))
    visitor_team_id = db.Column(db.Integer, db.ForeignKey('nba_teams.team_id'))
    home_team_score = db.Column(db.Integer)
    visitor_team_score = db.Column(db.Integer)

    home_team = db.relationship('NBATeam', foreign_keys=[home_team_id], back_populates='games_home')
    visitor_team = db.relationship('NBATeam', foreign_keys=[visitor_team_id], back_populates='games_away')

    __table_args__ = (
        db.CheckConstraint('home_team_score >= 0', name='ck_nba_game_home_score_non_negative'),
        db.CheckConstraint('visitor_team_score >= 0', name='ck_nba_game_visitor_score_non_negative'),
    )

    def __repr__(self):
        return f'<NBAGame {self.game_id}>'


class NHLGame(BaseModel):
    __tablename__ = 'nhl_games'

    game_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    season = db.Column(db.String(10))
    home_team_id = db.Column(db.Integer, db.ForeignKey('nhl_teams.team_id'))
    visitor_team_id = db.Column(db.Integer, db.ForeignKey('nhl_teams.team_id'))
    home_team_score = db.Column(db.Integer)
    visitor_team_score = db.Column(db.Integer)

    home_team = db.relationship('NHLTeam', foreign_keys=[home_team_id], back_populates='games_home')
    visitor_team = db.relationship('NHLTeam', foreign_keys=[visitor_team_id], back_populates='games_away')

    __table_args__ = (
        db.CheckConstraint('home_team_score >= 0', name='ck_nhl_game_home_score_non_negative'),
        db.CheckConstraint('visitor_team_score >= 0', name='ck_nhl_game_visitor_score_non_negative'),
    )

    def __repr__(self):
        return f'<NHLGame {self.game_id}>'
