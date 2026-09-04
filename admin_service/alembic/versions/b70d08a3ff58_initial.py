"""initial

Revision ID: b70d08a3ff58
Revises:
Create Date: 2026-08-19 16:09:41.600411
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b70d08a3ff58'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('surname', sa.String(), nullable=False),
        sa.Column('birthday', sa.DateTime(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('password', name='admin_password_key')
    )

    op.create_index(
        op.f('ix_admin_id'),
        'admin',
        ['id'],
        unique=False
    )

    op.create_index(
        op.f('ix_admin_name'),
        'admin',
        ['name'],
        unique=False
    )

    op.create_index(
        op.f('ix_admin_surname'),
        'admin',
        ['surname'],
        unique=False
    )

    op.create_index(
        op.f('ix_admin_birthday'),
        'admin',
        ['birthday'],
        unique=False
    )

    op.create_index(
        op.f('ix_admin_phone'),
        'admin',
        ['phone'],
        unique=False
    )

    op.create_index(
        op.f('ix_admin_email'),
        'admin',
        ['email'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_email'), table_name='admin')
    op.drop_index(op.f('ix_admin_phone'), table_name='admin')
    op.drop_index(op.f('ix_admin_birthday'), table_name='admin')
    op.drop_index(op.f('ix_admin_surname'), table_name='admin')
    op.drop_index(op.f('ix_admin_name'), table_name='admin')
    op.drop_index(op.f('ix_admin_id'), table_name='admin')

    op.drop_table('admin')
