"""add nba team and game tables

Revision ID: abcd1234add
Revises: c1fb64894ba8
Create Date: 2025-07-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abcd1234add'
down_revision = 'c1fb64894ba8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'nba_teams',
        sa.Column('team_id', sa.Integer(), primary_key=True),
        sa.Column('abbreviation', sa.String(length=10)),
        sa.Column('city', sa.String(length=50)),
        sa.Column('conference', sa.String(length=20)),
        sa.Column('division', sa.String(length=50)),
        sa.Column('full_name', sa.String(length=100)),
        sa.Column('name', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'nba_games',
        sa.Column('game_id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date()),
        sa.Column('season', sa.Integer()),
        sa.Column('home_team_id', sa.Integer(), sa.ForeignKey('nba_teams.team_id')),
        sa.Column('visitor_team_id', sa.Integer(), sa.ForeignKey('nba_teams.team_id')),
        sa.Column('home_team_score', sa.Integer()),
        sa.Column('visitor_team_score', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table('nba_games')
    op.drop_table('nba_teams')
