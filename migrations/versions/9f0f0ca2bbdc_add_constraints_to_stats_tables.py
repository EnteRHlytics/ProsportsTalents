"""add constraints to stats and game tables

Revision ID: 9f0f0ca2bbdc
Revises: ad4f9e2cb98b
Create Date: 2025-07-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9f0f0ca2bbdc'
down_revision = 'ad4f9e2cb98b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        'uq_season_stat_player_season_name',
        'season_stats',
        ['athlete_id', 'season', 'name'],
    )
    op.create_unique_constraint(
        'uq_game_stat_unique',
        'game_stats',
        ['athlete_id', 'game_id', 'name'],
    )

    op.create_check_constraint(
        'ck_game_home_score_non_negative',
        'games',
        'home_team_score >= 0'
    )
    op.create_check_constraint(
        'ck_game_visitor_score_non_negative',
        'games',
        'visitor_team_score >= 0'
    )
    op.create_check_constraint(
        'ck_nba_game_home_score_non_negative',
        'nba_games',
        'home_team_score >= 0'
    )
    op.create_check_constraint(
        'ck_nba_game_visitor_score_non_negative',
        'nba_games',
        'visitor_team_score >= 0'
    )
    bind = op.get_bind()
    if sa.inspect(bind).has_table('nhl_games'):
        op.create_check_constraint(
            'ck_nhl_game_home_score_non_negative',
            'nhl_games',
            'home_team_score >= 0'
        )
        op.create_check_constraint(
            'ck_nhl_game_visitor_score_non_negative',
            'nhl_games',
            'visitor_team_score >= 0'
        )


def downgrade():
    bind = op.get_bind()
    if sa.inspect(bind).has_table('nhl_games'):
        op.drop_constraint('ck_nhl_game_visitor_score_non_negative', 'nhl_games', type_='check')
        op.drop_constraint('ck_nhl_game_home_score_non_negative', 'nhl_games', type_='check')
    op.drop_constraint('ck_nba_game_visitor_score_non_negative', 'nba_games', type_='check')
    op.drop_constraint('ck_nba_game_home_score_non_negative', 'nba_games', type_='check')
    op.drop_constraint('ck_game_visitor_score_non_negative', 'games', type_='check')
    op.drop_constraint('ck_game_home_score_non_negative', 'games', type_='check')

    op.drop_constraint('uq_game_stat_unique', 'game_stats', type_='unique')
    op.drop_constraint('uq_season_stat_player_season_name', 'season_stats', type_='unique')

