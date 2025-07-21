"""Add notes field to payment order table

Revision ID: ced652350042
Revises: db4fc04622ef
Create Date: 2025-07-21 16:19:45.464132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = 'ced652350042'
down_revision: Union[str, None] = 'db4fc04622ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payment_order", sa.Column("notes", sa.Text(), nullable=True))



def downgrade() -> None:
    op.drop_column("payment_order", "notes")
