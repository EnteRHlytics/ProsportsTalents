"""add stat_type and season to athlete_stats

Revision ID: c1fb64894ba8
Revises: fa6e06b2cf59
Create Date: 2025-07-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1fb64894ba8'
down_revision = 'fa6e06b2cf59'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('athlete_stats', sa.Column('stat_type', sa.String(length=100), nullable=True))
    op.add_column('athlete_stats', sa.Column('season', sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column('athlete_stats', 'season')
    op.drop_column('athlete_stats', 'stat_type')
