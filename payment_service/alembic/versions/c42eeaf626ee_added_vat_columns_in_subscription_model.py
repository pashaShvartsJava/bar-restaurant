"""added vat columns in subscription model

Revision ID: c42eeaf626ee
Revises: 62de7a53d263
Create Date: 2026-11-10 19:47:38.962316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c42eeaf626ee'
down_revision: Union[str, Sequence[str], None] = '62de7a53d263'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    vat_status_enum = sa.Enum('NONE', 'VALID', 'INVALID', 'UNKNOWN', name='vatstatus')
    vat_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('subscriptions', sa.Column('vat_id', sa.String(length=20), nullable=True))
    op.add_column('subscriptions', sa.Column(
        'vat_status',
        vat_status_enum,
        nullable=False,
        server_default='NONE'))
    op.add_column('subscriptions', sa.Column('vat_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column(
        'country',
        sa.String(length=2),
        server_default='DE',
        nullable=False))
    op.create_index(op.f('ix_subscriptions_country'), 'subscriptions', ['country'], unique=False)
    op.create_index(op.f('ix_subscriptions_vat_id'), 'subscriptions', ['vat_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_subscriptions_vat_id'), table_name='subscriptions')
    op.drop_column('subscriptions', 'country')
    op.drop_column('subscriptions', 'vat_checked_at')
    op.drop_column('subscriptions', 'vat_status')
    op.drop_column('subscriptions', 'vat_id')
    sa.Enum(name='vatstatus').drop(op.get_bind(), checkfirst=True)
