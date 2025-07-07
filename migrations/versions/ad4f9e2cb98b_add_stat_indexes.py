"""add indexes for stat lookup

Revision ID: ad4f9e2cb98b
Revises: e6d6b9c8f7c9
Create Date: 2025-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ad4f9e2cb98b'
down_revision = 'e6d6b9c8f7c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('idx_stats_season', 'athlete_stats', ['season'])
    op.create_index('idx_stats_athlete_season', 'athlete_stats', ['athlete_id', 'season'])

    op.create_index('idx_season_stats_team', 'season_stats', ['team_id'])
    op.create_index('idx_season_stats_athlete_season', 'season_stats', ['athlete_id', 'season'])

    op.create_index('idx_game_stats_athlete', 'game_stats', ['athlete_id'])
    op.create_index('idx_game_stats_athlete_game', 'game_stats', ['athlete_id', 'game_id'])


def downgrade():
    op.drop_index('idx_game_stats_athlete_game', table_name='game_stats')
    op.drop_index('idx_game_stats_athlete', table_name='game_stats')

    op.drop_index('idx_season_stats_athlete_season', table_name='season_stats')
    op.drop_index('idx_season_stats_team', table_name='season_stats')

    op.drop_index('idx_stats_athlete_season', table_name='athlete_stats')
    op.drop_index('idx_stats_season', table_name='athlete_stats')
