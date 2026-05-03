"""add activity_logs table

Revision ID: a5b1c0d2e3f4
Revises: 7c4a91d3e5a2
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5b1c0d2e3f4'
down_revision = '7c4a91d3e5a2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('path', sa.String(length=2048), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('target_resource_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
    )
    op.create_index(
        'ix_activity_logs_user_id', 'activity_logs', ['user_id']
    )
    op.create_index(
        'ix_activity_logs_target_resource_id',
        'activity_logs',
        ['target_resource_id'],
    )
    op.create_index(
        'ix_activity_logs_created_at', 'activity_logs', ['created_at']
    )
    op.create_index(
        'idx_activity_user_created',
        'activity_logs',
        ['user_id', 'created_at'],
    )


def downgrade():
    op.drop_index('idx_activity_user_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_created_at', table_name='activity_logs')
    op.drop_index(
        'ix_activity_logs_target_resource_id', table_name='activity_logs'
    )
    op.drop_index('ix_activity_logs_user_id', table_name='activity_logs')
    op.drop_table('activity_logs')
