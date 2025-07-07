"""add indexes for name search

Revision ID: e8b9f47f3d4a
Revises: d963424f23ab
Create Date: 2025-08-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e8b9f47f3d4a'
down_revision = 'd963424f23ab'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('idx_users_first_name', 'users', ['first_name'])
    op.create_index('idx_users_last_name', 'users', ['last_name'])
    op.create_index('idx_athletes_current_team', 'athlete_profiles', ['current_team'])


def downgrade():
    op.drop_index('idx_athletes_current_team', table_name='athlete_profiles')
    op.drop_index('idx_users_last_name', table_name='users')
    op.drop_index('idx_users_first_name', table_name='users')

