"""add athlete skills table

Revision ID: cbacbef4e34e
Revises: 5bb8dbba77e3
Create Date: 2025-06-16 15:40:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = 'cbacbef4e34e'
down_revision = '5bb8dbba77e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'athlete_skills',
        sa.Column('skill_id', sa.String(length=36), primary_key=True),
        sa.Column('athlete_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('level', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['athlete_id'], ['athlete_profiles.athlete_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_skills_athlete', 'athlete_skills', ['athlete_id'])


def downgrade():
    op.drop_index('idx_skills_athlete', table_name='athlete_skills')
    op.drop_table('athlete_skills')

