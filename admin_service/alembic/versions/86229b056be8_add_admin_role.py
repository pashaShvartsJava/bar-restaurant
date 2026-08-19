"""add admin role

Revision ID: 86229b056be8
Revises: b70d08a3ff58
Create Date: 2026-08-19 16:21:50.178107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86229b056be8'
down_revision: Union[str, Sequence[str], None] = 'b70d08a3ff58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum(
        'ADMIN',
        'MODERATOR',
        name='role'
    )

    role_enum.create(op.get_bind())

    op.add_column(
        'admin',
        sa.Column(
            'role',
            role_enum,
            nullable=True
        )
    )

    op.execute(
        "UPDATE admin SET role = 'ADMIN' WHERE role IS NULL"
    )

    op.alter_column(
        'admin',
        'role',
        nullable=False
    )


def downgrade() -> None:
    op.drop_column('admin', 'role')

    role_enum = sa.Enum(
        'ADMIN',
        'MODERATOR',
        name='role'
    )

    role_enum.drop(op.get_bind())
