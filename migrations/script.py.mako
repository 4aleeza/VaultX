# =============================================================================
# SecureVault - Alembic Migration Script Template
# =============================================================================
# Template used by Alembic when generating new migration scripts.
# =============================================================================

"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    """Upgrade the database to this revision."""
    ${upgrades if upgrades else "pass"}


def downgrade():
    """Downgrade the database from this revision."""
    ${downgrades if downgrades else "pass"}
