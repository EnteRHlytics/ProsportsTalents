from app import db
from app.models.base import BaseModel
import uuid

class AthleteStat(BaseModel):
    __tablename__ = 'athlete_stats'

    stat_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = db.Column(db.String(36), db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100))
    stat_type = db.Column(db.String(100))
    season = db.Column(db.String(20))

    athlete = db.relationship('AthleteProfile', backref='stats')

    __table_args__ = (
        db.Index('idx_stats_athlete', 'athlete_id'),
        db.Index('idx_stats_season', 'season'),
        db.Index('idx_stats_athlete_season', 'athlete_id', 'season'),
    )

    def __repr__(self):
        return f'<AthleteStat {self.stat_id}>'


class SeasonStat(BaseModel):
    """Aggregated stats for a player during a specific season."""

    __tablename__ = 'season_stats'

    season_stat_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = db.Column(
        db.String(36), db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False
    )
    sport_id = db.Column(db.Integer, db.ForeignKey('sports.sport_id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'))
    season = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100))

    athlete = db.relationship('AthleteProfile')
    sport = db.relationship('Sport')
    team = db.relationship('Team')

    __table_args__ = (
        db.UniqueConstraint(
            'athlete_id',
            'season',
            'name',
            name='uq_season_stat_player_season_name',
        ),
        db.Index('idx_season_stats_athlete', 'athlete_id'),
        db.Index('idx_season_stats_season', 'season'),
        db.Index('idx_season_stats_team', 'team_id'),
        db.Index('idx_season_stats_athlete_season', 'athlete_id', 'season'),
    )

    def __repr__(self):
        return f'<SeasonStat {self.season_stat_id}>'


class GameStat(BaseModel):
    """Per-game statistics for an athlete."""

    __tablename__ = 'game_stats'

    game_stat_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    athlete_id = db.Column(
        db.String(36), db.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False
    )
    game_id = db.Column(db.Integer, db.ForeignKey('games.game_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100))

    athlete = db.relationship('AthleteProfile')
    game = db.relationship('Game')

    __table_args__ = (
        db.UniqueConstraint(
            'athlete_id',
            'game_id',
            'name',
            name='uq_game_stat_unique',
        ),
        db.Index('idx_game_stats_game', 'game_id'),
        db.Index('idx_game_stats_athlete', 'athlete_id'),
        db.Index('idx_game_stats_athlete_game', 'athlete_id', 'game_id'),
    )

    def __repr__(self):
        return f'<GameStat {self.game_stat_id}>'
