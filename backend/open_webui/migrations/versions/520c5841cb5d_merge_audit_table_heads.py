"""merge_audit_table_heads

Revision ID: 520c5841cb5d
Revises: 583813ee2359, add_payment_order_audit
Create Date: 2025-07-10 19:29:39.062367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '520c5841cb5d'
down_revision: Union[str, None] = ('583813ee2359', 'add_payment_order_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
