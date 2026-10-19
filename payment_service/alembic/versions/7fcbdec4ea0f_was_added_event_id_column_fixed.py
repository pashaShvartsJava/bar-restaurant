"""was added event_id column fixed

Revision ID: 7fcbdec4ea0f
Revises: bef8a0c60a7f
Create Date: 2026-09-24 10:17:46.242755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fcbdec4ea0f'
down_revision: Union[str, Sequence[str], None] = 'bef8a0c60a7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("TRUNCATE TABLE outbox_payment_events")

    op.alter_column(
        "outbox_payment_events",
        "event_id",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "outbox_payment_events",
        "event_id",
        existing_type=sa.String(),
        nullable=True,
    )