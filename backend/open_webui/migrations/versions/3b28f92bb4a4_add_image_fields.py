"""add image fields

Revision ID: 3b28f92bb4a4
Revises: b102593fcd39
Create Date: 2025-09-05 16:52:44.001169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '3b28f92bb4a4'
down_revision: Union[str, None] = 'b102593fcd39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_credit", sa.Column("image_credit_balance", sa.BigInteger(), nullable=True, server_default="0"))
    op.add_column("user_credit", sa.Column("video_credit_balance", sa.BigInteger(), nullable=True, server_default="0"))
    op.add_column("user_credit", sa.Column("monthly_image_quota", sa.BigInteger(), nullable=True, server_default="0"))
    op.add_column("user_credit", sa.Column("monthly_video_quota", sa.BigInteger(), nullable=True, server_default="0"))
    op.add_column("payment_order", sa.Column("image_credits", sa.BigInteger(), nullable=True, server_default="0"))
    op.add_column("payment_order", sa.Column("video_credits", sa.BigInteger(), nullable=True, server_default="0"))


def downgrade() -> None:
    op.drop_column("user_credit", "image_credit_balance")
    op.drop_column("user_credit", "video_credit_balance")
    op.drop_column("user_credit", "monthly_image_quota")
    op.drop_column("user_credit", "monthly_video_quota")
    op.drop_column("payment_order", "image_credits")
    op.drop_column("payment_order", "video_credits")

