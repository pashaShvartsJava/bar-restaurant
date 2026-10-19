"""add column status in identity table

Revision ID: 999850aaf85e
Revises: 21aff811a15d
Create Date: 2026-09-04 11:53:53.449582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '999850aaf85e'
down_revision: Union[str, Sequence[str], None] = '21aff811a15d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = sa.Enum(
        'ACTIVE',
        'PENDING',
        'FAILED',
        'BLOCKED',
        name='status'
    )

    status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'identity',
        sa.Column(
            'status',
            status_enum,
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('identity', 'status')

    status_enum = sa.Enum(
        'ACTIVE',
        'PENDING',
        'FAILED',
        'BLOCKED',
        name='status'
    )

    status_enum.drop(op.get_bind(), checkfirst=True)