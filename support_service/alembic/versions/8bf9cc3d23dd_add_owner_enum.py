"""add owner enum

Revision ID: 8bf9cc3d23dd
Revises: 19e705a5d685
Create Date: 2026-10-29 18:06:24.766426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bf9cc3d23dd'
down_revision: Union[str, Sequence[str], None] = '19e705a5d685'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE senderrole ADD VALUE IF NOT EXISTS 'OWNER'")


def downgrade() -> None:
    pass
