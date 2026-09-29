"""add session_version to users

Revision ID: a6c3d1e2f3a4
Revises: a1b2c3d4e5f6
Create Date: 2026-08-26 00:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6c3d1e2f3a4'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade the database to this revision."""
    # Add the server-authoritative per-user session-generation counter. The
    # server_default backfills all existing rows to 0, so the column can be
    # added as NOT NULL safely on populated databases.
    op.add_column(
        'users',
        sa.Column('session_version', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade():
    """Downgrade the database from this revision."""
    op.drop_column('users', 'session_version')
