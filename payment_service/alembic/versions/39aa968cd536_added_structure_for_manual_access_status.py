"""added structure for manual access status

Revision ID: 39aa968cd536
Revises: a092d74cd202
Create Date: 2026-11-18 17:46:44.411894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '39aa968cd536'
down_revision: Union[str, Sequence[str], None] = 'a092d74cd202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Создаём PostgreSQL Enum до добавления колонки
    access_status_enum = sa.Enum(
        'ENABLED',
        'SUSPENDED',
        name='accessstatus'
    )

    access_status_enum.create(op.get_bind(), checkfirst=True)

    # Добавляем статус доступа
    op.add_column(
        'subscriptions',
        sa.Column(
            'access_status',
            access_status_enum,
            nullable=False,
            server_default='ENABLED'
        )
    )

    # Добавляем информацию о ручной приостановке
    op.add_column(
        'subscriptions',
        sa.Column('suspended_reason', sa.Text(), nullable=True)
    )

    op.add_column(
        'subscriptions',
        sa.Column(
            'suspended_at',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        'subscriptions',
        sa.Column('suspended_by', sa.String(), nullable=True)
    )

    # Убираем default после заполнения существующих записей
    op.alter_column(
        'subscriptions',
        'access_status',
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('subscriptions', 'suspended_by')
    op.drop_column('subscriptions', 'suspended_at')
    op.drop_column('subscriptions', 'suspended_reason')
    op.drop_column('subscriptions', 'access_status')

    # Удаляем PostgreSQL Enum
    sa.Enum(
        'ENABLED',
        'SUSPENDED',
        name='accessstatus'
    ).drop(op.get_bind(), checkfirst=True)
