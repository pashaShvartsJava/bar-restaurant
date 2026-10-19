"""add column email in admin table

Revision ID: 745c2d1b46d8
Revises: 08eed403d456
Create Date: 2026-09-07 09:57:15.843498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '745c2d1b46d8'
down_revision: Union[str, Sequence[str], None] = '08eed403d456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'admin',
        sa.Column('email', sa.String(), nullable=False)
    )
    op.create_index(
        op.f('ix_admin_email'),
        'admin',
        ['email'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_admin_email'),
        table_name='admin'
    )
    op.drop_column('admin', 'email')
