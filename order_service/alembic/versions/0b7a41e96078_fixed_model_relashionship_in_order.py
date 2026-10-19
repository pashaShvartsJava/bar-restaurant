"""fixed model relashionship in order

Revision ID: 0b7a41e96078
Revises: 600553ca643f
Create Date: 2026-09-18 16:32:46.129105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b7a41e96078'
down_revision: Union[str, Sequence[str], None] = '600553ca643f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
