"""Add contract_active column to athlete_profiles

Revision ID: b183ac0d37f0
Revises: 9f0f0ca2bbdc
Create Date: 2025-07-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b183ac0d37f0'
down_revision = '9f0f0ca2bbdc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.add_column(sa.Column('contract_active', sa.Boolean(), server_default=sa.text('true')))


def downgrade():
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.drop_column('contract_active')
