"""Add is_deleted column to athlete_profiles

Revision ID: 90e86a8e8360
Revises: 5bb8dbba77e3
Create Date: 2025-06-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '90e86a8e8360'
down_revision = '5bb8dbba77e3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false')))
        batch_op.create_index(batch_op.f('idx_athletes_deleted'), ['is_deleted'], unique=False)


def downgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.drop_index(batch_op.f('idx_athletes_deleted'))
        batch_op.drop_column('is_deleted')
