"""add saved_searches table

Revision ID: a2c4e1d9b0f5
Revises: f29d5d6ebc1b
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = 'a2c4e1d9b0f5'
down_revision = 'f29d5d6ebc1b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('params_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', name='uq_saved_search_user_name'),
    )
    op.create_index('idx_saved_searches_user', 'saved_searches', ['user_id'])
    op.create_index(
        'ix_saved_searches_created_at', 'saved_searches', ['created_at']
    )
    op.create_index(
        'ix_saved_searches_updated_at', 'saved_searches', ['updated_at']
    )


def downgrade():
    op.drop_index('ix_saved_searches_updated_at', table_name='saved_searches')
    op.drop_index('ix_saved_searches_created_at', table_name='saved_searches')
    op.drop_index('idx_saved_searches_user', table_name='saved_searches')
    op.drop_table('saved_searches')
