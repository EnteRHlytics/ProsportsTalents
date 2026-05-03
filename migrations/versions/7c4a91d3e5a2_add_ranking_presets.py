"""Add ranking_presets table

Revision ID: 7c4a91d3e5a2
Revises: a2c4e1d9b0f5
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c4a91d3e5a2'
down_revision = 'a2c4e1d9b0f5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ranking_presets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('sport_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('weights_json', sa.Text(), nullable=False),
        sa.Column(
            'is_default',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.user_id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['sport_id'], ['sports.sport_id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'sport_id', 'name', name='uq_ranking_preset_name'
        ),
    )
    op.create_index(
        'idx_ranking_presets_user', 'ranking_presets', ['user_id']
    )
    op.create_index(
        'idx_ranking_presets_user_sport',
        'ranking_presets',
        ['user_id', 'sport_id'],
    )


def downgrade():
    op.drop_index('idx_ranking_presets_user_sport', table_name='ranking_presets')
    op.drop_index('idx_ranking_presets_user', table_name='ranking_presets')
    op.drop_table('ranking_presets')
