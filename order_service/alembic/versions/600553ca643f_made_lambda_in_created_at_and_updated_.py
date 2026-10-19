"""made lambda in created at and updated at fields

Revision ID: 600553ca643f
Revises: 4d5a93b2960e
Create Date: 2026-09-18 13:39:15.814339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '600553ca643f'
down_revision: Union[str, Sequence[str], None] = '4d5a93b2960e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
