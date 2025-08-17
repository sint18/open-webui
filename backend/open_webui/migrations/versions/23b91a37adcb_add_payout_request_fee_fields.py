"""add payout requested_amount fee_mmk details"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '23b91a37adcb'
down_revision = 'f7e8308eaa9c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payout', sa.Column('details', sa.Text(), nullable=True), schema='affiliate')
    op.add_column('payout', sa.Column('requested_amount', sa.Numeric(), nullable=False, server_default='0'), schema='affiliate')
    op.add_column('payout', sa.Column('fee_mmk', sa.Numeric(), nullable=False, server_default='0'), schema='affiliate')


def downgrade():
    op.drop_column('payout', 'fee_mmk', schema='affiliate')
    op.drop_column('payout', 'requested_amount', schema='affiliate')
    op.drop_column('payout', 'details', schema='affiliate')
