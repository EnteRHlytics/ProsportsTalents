"""Add is_featured column to athlete_profiles

Revision ID: d963424f23ab
Revises: b183ac0d37f0
Create Date: 2025-07-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd963424f23ab'
down_revision = 'b183ac0d37f0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.add_column(sa.Column('is_featured', sa.Boolean(), server_default=sa.text('false')))


def downgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.drop_column('is_featured')
