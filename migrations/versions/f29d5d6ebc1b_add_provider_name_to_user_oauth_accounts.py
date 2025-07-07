"""add provider_name to user_oauth_accounts

Revision ID: f29d5d6ebc1b
Revises: e8b9f47f3d4a
Create Date: 2025-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f29d5d6ebc1b'
down_revision = 'e8b9f47f3d4a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_oauth_accounts', sa.Column('provider_name', sa.String(length=50), nullable=True))

    conn = op.get_bind()
    if conn.dialect.has_table(conn, 'oauth_providers'):
        conn.execute(sa.text(
            "UPDATE user_oauth_accounts u SET provider_name = p.provider_name "
            "FROM oauth_providers p WHERE u.provider_id = p.provider_id"
        ))

    op.alter_column('user_oauth_accounts', 'provider_name', nullable=False)

    op.drop_constraint('uq_provider_user', 'user_oauth_accounts', type_='unique')
    op.create_unique_constraint('uq_provider_user', 'user_oauth_accounts', ['provider_name', 'provider_user_id'])

    with op.batch_alter_table('user_oauth_accounts') as batch_op:
        batch_op.drop_index('idx_oauth_user_provider')
        batch_op.create_index('idx_oauth_user_provider_name', ['user_id', 'provider_name'])


def downgrade():
    with op.batch_alter_table('user_oauth_accounts') as batch_op:
        batch_op.drop_index('idx_oauth_user_provider_name')
        batch_op.create_index('idx_oauth_user_provider', ['user_id', 'provider_id'])

    op.drop_constraint('uq_provider_user', 'user_oauth_accounts', type_='unique')
    op.create_unique_constraint('uq_provider_user', 'user_oauth_accounts', ['provider_id', 'provider_user_id'])

    op.drop_column('user_oauth_accounts', 'provider_name')
