"""create guest customers table

Revision ID: c018a001ff4c
Revises: 78f4a625469a
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c018a001ff4c"
down_revision: Union[str, Sequence[str], None] = "78f4a625469a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guest_customers",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "surname",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "birthday",
            sa.Date(),
            nullable=False,
        ),

        sa.Column(
            "phone",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.UniqueConstraint(
            "client_id",
            name="uq_guest_customers_client_id",
        ),
    )

    op.create_index(
        "ix_guest_customers_id",
        "guest_customers",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_guest_customers_client_id",
        "guest_customers",
        ["client_id"],
        unique=False,
    )

    op.create_index(
        "ix_guest_customers_name",
        "guest_customers",
        ["name"],
        unique=False,
    )

    op.create_index(
        "ix_guest_customers_surname",
        "guest_customers",
        ["surname"],
        unique=False,
    )

    op.create_index(
        "ix_guest_customers_birthday",
        "guest_customers",
        ["birthday"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_guest_customers_birthday",
        table_name="guest_customers",
    )

    op.drop_index(
        "ix_guest_customers_surname",
        table_name="guest_customers",
    )

    op.drop_index(
        "ix_guest_customers_name",
        table_name="guest_customers",
    )

    op.drop_index(
        "ix_guest_customers_client_id",
        table_name="guest_customers",
    )

    op.drop_index(
        "ix_guest_customers_id",
        table_name="guest_customers",
    )

    op.drop_table("guest_customers")
