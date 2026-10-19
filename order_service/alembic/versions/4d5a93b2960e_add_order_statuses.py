"""add order statuses

Revision ID: 4d5a93b2960e
Revises: 1ec74d970b3d
Create Date: 2026-09-18 11:49:27.755460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d5a93b2960e'
down_revision: Union[str, Sequence[str], None] = '1ec74d970b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'CONFIRMED_ADDRESS'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'CANCELLED_BEFORE'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'CANCELLED_AFTER'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'EXPIRED'")



def downgrade() -> None:
    """Downgrade schema."""
    pass
