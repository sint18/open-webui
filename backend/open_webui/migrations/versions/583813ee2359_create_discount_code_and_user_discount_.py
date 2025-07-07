"""create discount_code and user_discount tables

Revision ID: 583813ee2359
Revises: b539b26ab39d
Create Date: 2025-07-07 15:06:37.499856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '583813ee2359'
down_revision: Union[str, None] = 'b539b26ab39d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create discount_code table
    op.create_table(
        "discount_code",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), default=0, server_default="0", nullable=False),
        sa.Column("active", sa.Boolean(), default=True, server_default="true", nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Create user_discount table
    op.create_table(
        "user_discount",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("discount_code", sa.String(), nullable=False),
        sa.Column("applied_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["discount_code"], ["discount_code.code"])
    )


def downgrade() -> None:
    op.drop_table("user_discount")
    op.drop_table("discount_code")
