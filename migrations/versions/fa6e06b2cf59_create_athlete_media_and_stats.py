"""create athlete media and stats tables

Revision ID: fa6e06b2cf59
Revises: 915b1c8b9adb
Create Date: 2025-07-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fa6e06b2cf59'
down_revision = '915b1c8b9adb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'athlete_media',
        sa.Column('media_id', sa.String(length=36), primary_key=True),
        sa.Column('athlete_id', sa.String(length=36), nullable=False),
        sa.Column('media_type', sa.String(length=20)),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['athlete_id'], ['athlete_profiles.athlete_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_media_athlete', 'athlete_media', ['athlete_id'])

    op.create_table(
        'athlete_stats',
        sa.Column('stat_id', sa.String(length=36), primary_key=True),
        sa.Column('athlete_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['athlete_id'], ['athlete_profiles.athlete_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_stats_athlete', 'athlete_stats', ['athlete_id'])


def downgrade():
    op.drop_index('idx_stats_athlete', table_name='athlete_stats')
    op.drop_table('athlete_stats')

    op.drop_index('idx_media_athlete', table_name='athlete_media')
    op.drop_table('athlete_media')
