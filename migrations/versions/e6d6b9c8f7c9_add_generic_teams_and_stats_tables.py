"""add generic teams and stats tables

Revision ID: e6d6b9c8f7c9
Revises: abcd1234add
Create Date: 2025-07-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e6d6b9c8f7c9'
down_revision = 'abcd1234add'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'teams',
        sa.Column('team_id', sa.Integer(), primary_key=True),
        sa.Column('sport_id', sa.Integer(), sa.ForeignKey('sports.sport_id'), nullable=False),
        sa.Column('abbreviation', sa.String(length=10)),
        sa.Column('city', sa.String(length=100)),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('league', sa.String(length=50)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_teams_sport', 'teams', ['sport_id'])

    op.create_table(
        'games',
        sa.Column('game_id', sa.Integer(), primary_key=True),
        sa.Column('sport_id', sa.Integer(), sa.ForeignKey('sports.sport_id'), nullable=False),
        sa.Column('season', sa.String(length=10)),
        sa.Column('date', sa.Date()),
        sa.Column('home_team_id', sa.Integer(), sa.ForeignKey('teams.team_id')),
        sa.Column('visitor_team_id', sa.Integer(), sa.ForeignKey('teams.team_id')),
        sa.Column('home_team_score', sa.Integer()),
        sa.Column('visitor_team_score', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_games_sport_season', 'games', ['sport_id', 'season'])

    op.create_table(
        'season_stats',
        sa.Column('season_stat_id', sa.String(length=36), primary_key=True),
        sa.Column('athlete_id', sa.String(length=36), sa.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False),
        sa.Column('sport_id', sa.Integer(), sa.ForeignKey('sports.sport_id'), nullable=False),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.team_id')),
        sa.Column('season', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_season_stats_athlete', 'season_stats', ['athlete_id'])
    op.create_index('idx_season_stats_season', 'season_stats', ['season'])

    op.create_table(
        'game_stats',
        sa.Column('game_stat_id', sa.String(length=36), primary_key=True),
        sa.Column('athlete_id', sa.String(length=36), sa.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'), nullable=False),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.game_id'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_game_stats_game', 'game_stats', ['game_id'])


def downgrade():
    op.drop_index('idx_game_stats_game', table_name='game_stats')
    op.drop_table('game_stats')

    op.drop_index('idx_season_stats_season', table_name='season_stats')
    op.drop_index('idx_season_stats_athlete', table_name='season_stats')
    op.drop_table('season_stats')

    op.drop_index('idx_games_sport_season', table_name='games')
    op.drop_table('games')

    op.drop_index('idx_teams_sport', table_name='teams')
    op.drop_table('teams')
