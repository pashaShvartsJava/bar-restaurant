"""added in messages new SenderRole as SUPERADMIN

Revision ID: e649961fa7bd
Revises: 659b6ea47e72
Create Date: 2026-11-20 19:33:11.561343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e649961fa7bd'
down_revision: Union[str, Sequence[str], None] = '659b6ea47e72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE senderrole ADD VALUE IF NOT EXISTS 'SUPERADMIN'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
