from alembic import op
import sqlalchemy as sa


revision = "a9bedd6c41ee"
down_revision = "81e23ae5b0fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "supplies",
        sa.Column("reason", sa.String(), nullable=False, server_default="")
    )


def downgrade() -> None:
    op.drop_column("supplies", "reason")