"""add salary/endorsement columns to athletes and fan_perception_scores table

Revision ID: b7c2d3e4f501
Revises: b6c2f4d7e1a8
Create Date: 2026-05-02 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c2d3e4f501'
down_revision = 'b6c2f4d7e1a8'
branch_labels = None
depends_on = None


def upgrade():
    # Agency-input market value columns on athlete_profiles.
    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.add_column(
            sa.Column('salary_usd', sa.Numeric(12, 2), nullable=True)
        )
        batch_op.add_column(
            sa.Column('endorsements_usd', sa.Numeric(12, 2), nullable=True)
        )
        batch_op.add_column(
            sa.Column('contract_end_date', sa.Date(), nullable=True)
        )

    # Cache table for computed fan-perception scores.  We cache to avoid
    # hitting Wikipedia / Reddit on every ranking calculation; the nightly
    # scheduler refreshes rows.
    op.create_table(
        'fan_perception_scores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'athlete_id',
            sa.String(length=36),
            sa.ForeignKey('athlete_profiles.athlete_id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('score', sa.Numeric(5, 2), nullable=False),
        sa.Column('source_breakdown', sa.Text(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(
        'ix_fan_perception_scores_athlete_id',
        'fan_perception_scores',
        ['athlete_id'],
    )
    op.create_index(
        'ix_fan_perception_scores_computed_at',
        'fan_perception_scores',
        ['computed_at'],
    )


def downgrade():
    op.drop_index(
        'ix_fan_perception_scores_computed_at',
        table_name='fan_perception_scores',
    )
    op.drop_index(
        'ix_fan_perception_scores_athlete_id',
        table_name='fan_perception_scores',
    )
    op.drop_table('fan_perception_scores')

    with op.batch_alter_table('athlete_profiles') as batch_op:
        batch_op.drop_column('contract_end_date')
        batch_op.drop_column('endorsements_usd')
        batch_op.drop_column('salary_usd')
