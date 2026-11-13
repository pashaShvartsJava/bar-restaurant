"""edit enum values in subscriptions

Revision ID: 1d572b77851e
Revises: c42eeaf626ee
Create Date: 2026-11-13 15:23:18.016931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1d572b77851e'
down_revision: Union[str, Sequence[str], None] = 'c42eeaf626ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'subscriptions', 'vat_status',
        existing_type=postgresql.ENUM('NONE', 'VALID', 'INVALID', 'UNKNOWN', name='vatstatus'),
        server_default=None,
        existing_nullable=False
    )
    op.execute("ALTER TYPE planid ADD VALUE IF NOT EXISTS 'basic'")
    op.execute("ALTER TYPE planid ADD VALUE IF NOT EXISTS 'online'")


def downgrade() -> None:
    op.execute("UPDATE subscriptions SET plan_id = 'starter' WHERE plan_id = 'basic'")
    op.alter_column(
        'subscriptions', 'vat_status',
        existing_type=postgresql.ENUM('NONE', 'VALID', 'INVALID', 'UNKNOWN', name='vatstatus'),
        server_default=sa.text("'NONE'::vatstatus"),
        existing_nullable=False
    )
