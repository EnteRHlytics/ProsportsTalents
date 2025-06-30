"""Replace user status enum with is_active boolean

Revision ID: 915b1c8b9adb
Revises: 5bb8dbba77e3
Create Date: 2025-06-27 18:32:32.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '915b1c8b9adb'
down_revision = '5bb8dbba77e3'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_active column with default True
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')))

    # Migrate data from status to is_active
    op.execute("UPDATE users SET is_active = CASE WHEN status = 'ACTIVE' THEN TRUE ELSE FALSE END")

    # Drop indexes that reference status
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('idx_users_username_status')
        batch_op.drop_index('idx_users_email_status')

    # Drop status column
    op.drop_column('users', 'status')

    # Drop enum type if using PostgreSQL
    op.execute("DROP TYPE IF EXISTS userstatus")


def downgrade():
    # Recreate enum type and status column
    user_status = postgresql.ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING', name='userstatus')
    user_status.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column('status', user_status, nullable=False, server_default='ACTIVE'))

    # Migrate data back from is_active
    op.execute("UPDATE users SET status = CASE WHEN is_active THEN 'ACTIVE' ELSE 'INACTIVE' END")

    # Recreate indexes using status
    with op.batch_alter_table('users') as batch_op:
        batch_op.create_index('idx_users_username_status', ['username', 'status'])
        batch_op.create_index('idx_users_email_status', ['email', 'status'])

    # Drop is_active column
    op.drop_column('users', 'is_active')
