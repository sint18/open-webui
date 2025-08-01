"""add necessary fields to tables

Revision ID: 75bf1ad9fa37
Revises: 6f18ba5e848e
Create Date: 2025-07-30 22:54:54.944364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '75bf1ad9fa37'
down_revision: Union[str, None] = '6f18ba5e848e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("image_job", sa.Column("meta", sa.JSON(), nullable=True))
    op.add_column("credit_transaction", sa.Column("resource_type", sa.String(), nullable=True))
    op.add_column("credit_transaction", sa.Column("reference_id", sa.String(), nullable=True))
    op.add_column("credit_transaction", sa.Column("meta", sa.JSON(), nullable=True))



def downgrade() -> None:
    op.drop_column("credit_transaction", "resource_type")
    op.drop_column("credit_transaction", "reference_id")
    op.drop_column("credit_transaction", "meta")
    op.drop_column("image_job", "meta")

