"""add unique constraint to affiliate.commission"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1f274b967a3'
down_revision: Union[str, None] = 'f7e8308eaa9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_commission_order_partner_type',
        'commission',
        ['order_id', 'partner_id', 'type'],
        schema='affiliate',
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_commission_order_partner_type',
        'commission',
        type_='unique',
        schema='affiliate',
    )
