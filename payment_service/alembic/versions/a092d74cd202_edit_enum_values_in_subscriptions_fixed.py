"""edit enum values in subscriptions fixed

Revision ID: a092d74cd202
Revises: 1d572b77851e
Create Date: 2026-11-13 15:41:45.047442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a092d74cd202'
down_revision: Union[str, Sequence[str], None] = '1d572b77851e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'subscriptions', 'vat_status',
        existing_type=postgresql.ENUM('NONE', 'VALID', 'INVALID', 'UNKNOWN', name='vatstatus'),
        server_default=None,
        existing_nullable=False
    )
    op.execute("ALTER TYPE planid ADD VALUE IF NOT EXISTS 'BASIC'")
    op.execute("ALTER TYPE planid ADD VALUE IF NOT EXISTS 'ONLINE'")


def downgrade() -> None:
    op.alter_column(
        'subscriptions', 'vat_status',
        existing_type=postgresql.ENUM('NONE', 'VALID', 'INVALID', 'UNKNOWN', name='vatstatus'),
        server_default=sa.text("'NONE'::vatstatus"),
        existing_nullable=False
    )
