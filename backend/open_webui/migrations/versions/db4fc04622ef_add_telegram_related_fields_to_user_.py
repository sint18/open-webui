"""Add telegram related fields to user table

Revision ID: db4fc04622ef
Revises: 520c5841cb5d
Create Date: 2025-07-20 18:54:34.741665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = 'db4fc04622ef'
down_revision: Union[str, None] = '520c5841cb5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('telegram_chat_id', sa.String(), nullable=True))
    op.add_column('user', sa.Column('telegram_onboarding_token', sa.String(), nullable=True))
    op.add_column('user', sa.Column('telegram_onboarding_token_expires_at', sa.BigInteger(), nullable=True))

    op.create_unique_constraint( None,'user', ['telegram_chat_id'])
    op.create_unique_constraint(None, 'user', ['telegram_onboarding_token'])


def downgrade() -> None:
    op.drop_column('user', 'telegram_onboarding_token_expires_at')
    op.drop_column('user', 'telegram_onboarding_token')
    op.drop_column('user', 'telegram_chat_id')
