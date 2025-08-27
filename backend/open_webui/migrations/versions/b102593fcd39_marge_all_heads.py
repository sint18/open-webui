"""empty message

Revision ID: b102593fcd39
Revises: 75bf1ad9fa37, c59a1d734f9a, c8b9f0e5b6e2, cf5f9d1eabc1
Create Date: 2025-08-27 14:01:58.900516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = 'b102593fcd39'
down_revision: Union[str, None] = ('cf5f9d1eabc1', 'c59a1d734f9a', 'c8b9f0e5b6e2', '75bf1ad9fa37')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
