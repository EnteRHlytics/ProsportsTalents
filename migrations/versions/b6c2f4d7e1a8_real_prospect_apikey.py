"""replace prospect/api_key stubs with real schemas

Revision ID: b6c2f4d7e1a8
Revises: a5b1c0d2e3f4
Create Date: 2026-05-02 00:00:00.000000

This migration replaces the Wave-1 minimal stub tables for
``prospects``, ``prospect_leagues``, ``minor_league_teams``,
``prospect_stats`` and ``api_keys`` with the production schemas
described in ``app/models/prospect.py`` and ``app/models/api_key.py``.

Because the stub tables only existed in dev databases (and used a
different column shape), we drop them up-front and recreate them with
the real columns. Production deployments where the stubs were never
applied will simply create the new tables.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6c2f4d7e1a8'
down_revision = 'a5b1c0d2e3f4'
branch_labels = None
depends_on = None


def _drop_stub_tables() -> None:
    """Drop the stub prospect/api_key tables if they exist.

    The stubs predate this migration so cannot be migrated in-place
    (column types and PKs differ). Dropping is safe in dev/test; in
    production the stubs were never deployed.
    """
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else 'sqlite'

    for table in (
        'prospect_stats',
        'prospects',
        'minor_league_teams',
        'prospect_leagues',
        'api_keys',
    ):
        if dialect == 'postgresql':
            op.execute(sa.text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        else:
            op.execute(sa.text(f'DROP TABLE IF EXISTS {table}'))


def upgrade():
    _drop_stub_tables()

    op.create_table(
        'prospect_leagues',
        sa.Column('prospect_league_id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('sport_id', sa.Integer(), nullable=True),
        sa.Column(
            'is_pro_pipeline', sa.Boolean(), nullable=False,
            server_default=sa.true(),
        ),
        sa.Column('country', sa.String(length=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sport_id'], ['sports.sport_id']),
        sa.UniqueConstraint('code', name='uq_prospect_leagues_code'),
    )
    op.create_index(
        'ix_prospect_leagues_code', 'prospect_leagues', ['code'], unique=True
    )
    op.create_index(
        'ix_prospect_leagues_sport_id', 'prospect_leagues', ['sport_id']
    )
    op.create_index(
        'ix_prospect_leagues_created_at', 'prospect_leagues', ['created_at']
    )
    op.create_index(
        'ix_prospect_leagues_updated_at', 'prospect_leagues', ['updated_at']
    )

    op.create_table(
        'minor_league_teams',
        sa.Column('team_id', sa.String(length=36), primary_key=True),
        sa.Column('prospect_league_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('abbreviation', sa.String(length=10), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('external_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['prospect_league_id'], ['prospect_leagues.prospect_league_id'],
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint(
            'prospect_league_id', 'external_id',
            name='uq_minor_league_team_league_external',
        ),
    )
    op.create_index(
        'ix_minor_league_teams_prospect_league_id',
        'minor_league_teams', ['prospect_league_id'],
    )
    op.create_index(
        'ix_minor_league_teams_external_id',
        'minor_league_teams', ['external_id'],
    )
    op.create_index(
        'ix_minor_league_teams_created_at', 'minor_league_teams', ['created_at']
    )
    op.create_index(
        'ix_minor_league_teams_updated_at', 'minor_league_teams', ['updated_at']
    )

    op.create_table(
        'prospects',
        sa.Column('prospect_id', sa.String(length=36), primary_key=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('height_cm', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Numeric(5, 2), nullable=True),
        sa.Column('primary_sport_id', sa.Integer(), nullable=True),
        sa.Column('primary_position_id', sa.Integer(), nullable=True),
        sa.Column('current_team_id', sa.String(length=36), nullable=True),
        sa.Column('prospect_league_id', sa.String(length=36), nullable=True),
        sa.Column('school', sa.String(length=150), nullable=True),
        sa.Column('draft_eligible_year', sa.Integer(), nullable=True),
        sa.Column('scout_grade', sa.Integer(), nullable=True),
        sa.Column('scout_notes', sa.Text(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column(
            'is_deleted', sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ),
        sa.Column('external_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['primary_sport_id'], ['sports.sport_id']),
        sa.ForeignKeyConstraint(
            ['primary_position_id'], ['positions.position_id']
        ),
        sa.ForeignKeyConstraint(
            ['current_team_id'], ['minor_league_teams.team_id'],
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['prospect_league_id'], ['prospect_leagues.prospect_league_id'],
            ondelete='SET NULL',
        ),
        sa.CheckConstraint(
            'height_cm IS NULL OR (height_cm BETWEEN 100 AND 250)',
            name='ck_prospect_height_reasonable',
        ),
        sa.CheckConstraint(
            'weight_kg IS NULL OR (weight_kg BETWEEN 30 AND 200)',
            name='ck_prospect_weight_reasonable',
        ),
        sa.CheckConstraint(
            'scout_grade IS NULL OR (scout_grade BETWEEN 0 AND 100)',
            name='ck_prospect_scout_grade_range',
        ),
    )
    op.create_index('idx_prospects_name', 'prospects', ['last_name', 'first_name'])
    op.create_index('ix_prospects_primary_sport_id', 'prospects', ['primary_sport_id'])
    op.create_index('ix_prospects_current_team_id', 'prospects', ['current_team_id'])
    op.create_index('ix_prospects_prospect_league_id', 'prospects', ['prospect_league_id'])
    op.create_index('ix_prospects_draft_eligible_year', 'prospects', ['draft_eligible_year'])
    op.create_index('ix_prospects_is_deleted', 'prospects', ['is_deleted'])
    op.create_index('ix_prospects_external_id', 'prospects', ['external_id'])
    op.create_index('ix_prospects_created_at', 'prospects', ['created_at'])
    op.create_index('ix_prospects_updated_at', 'prospects', ['updated_at'])

    op.create_table(
        'prospect_stats',
        sa.Column('prospect_stat_id', sa.String(length=36), primary_key=True),
        sa.Column('prospect_id', sa.String(length=36), nullable=False),
        sa.Column('season', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('value', sa.String(length=120), nullable=True),
        sa.Column('stat_type', sa.String(length=40), nullable=True),
        sa.Column('source', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['prospect_id'], ['prospects.prospect_id'], ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'prospect_id', 'season', 'name',
            name='uq_prospect_stat_season_name',
        ),
    )
    op.create_index(
        'idx_prospect_stat_prospect_season',
        'prospect_stats', ['prospect_id', 'season'],
    )
    op.create_index('ix_prospect_stats_prospect_id', 'prospect_stats', ['prospect_id'])
    op.create_index('ix_prospect_stats_created_at', 'prospect_stats', ['created_at'])
    op.create_index('ix_prospect_stats_updated_at', 'prospect_stats', ['updated_at'])

    op.create_table(
        'api_keys',
        sa.Column('api_key_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.user_id'], ondelete='CASCADE'
        ),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('ix_api_keys_created_at', 'api_keys', ['created_at'])
    op.create_index('ix_api_keys_updated_at', 'api_keys', ['updated_at'])


def downgrade():
    op.drop_index('ix_api_keys_updated_at', table_name='api_keys')
    op.drop_index('ix_api_keys_created_at', table_name='api_keys')
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')

    op.drop_index('ix_prospect_stats_updated_at', table_name='prospect_stats')
    op.drop_index('ix_prospect_stats_created_at', table_name='prospect_stats')
    op.drop_index('ix_prospect_stats_prospect_id', table_name='prospect_stats')
    op.drop_index('idx_prospect_stat_prospect_season', table_name='prospect_stats')
    op.drop_table('prospect_stats')

    op.drop_index('ix_prospects_updated_at', table_name='prospects')
    op.drop_index('ix_prospects_created_at', table_name='prospects')
    op.drop_index('ix_prospects_external_id', table_name='prospects')
    op.drop_index('ix_prospects_is_deleted', table_name='prospects')
    op.drop_index('ix_prospects_draft_eligible_year', table_name='prospects')
    op.drop_index('ix_prospects_prospect_league_id', table_name='prospects')
    op.drop_index('ix_prospects_current_team_id', table_name='prospects')
    op.drop_index('ix_prospects_primary_sport_id', table_name='prospects')
    op.drop_index('idx_prospects_name', table_name='prospects')
    op.drop_table('prospects')

    op.drop_index('ix_minor_league_teams_updated_at', table_name='minor_league_teams')
    op.drop_index('ix_minor_league_teams_created_at', table_name='minor_league_teams')
    op.drop_index('ix_minor_league_teams_external_id', table_name='minor_league_teams')
    op.drop_index('ix_minor_league_teams_prospect_league_id', table_name='minor_league_teams')
    op.drop_table('minor_league_teams')

    op.drop_index('ix_prospect_leagues_updated_at', table_name='prospect_leagues')
    op.drop_index('ix_prospect_leagues_created_at', table_name='prospect_leagues')
    op.drop_index('ix_prospect_leagues_sport_id', table_name='prospect_leagues')
    op.drop_index('ix_prospect_leagues_code', table_name='prospect_leagues')
    op.drop_table('prospect_leagues')
