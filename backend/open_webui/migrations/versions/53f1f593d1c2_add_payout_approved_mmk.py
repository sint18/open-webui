"""add approved_mmk to payout"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '53f1f593d1c2'
down_revision = '23b91a37adcb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'payout',
        sa.Column('approved_mmk', sa.Numeric(12, 2), nullable=True),
        schema='affiliate',
    )


def downgrade():
    op.drop_column('payout', 'approved_mmk', schema='affiliate')
