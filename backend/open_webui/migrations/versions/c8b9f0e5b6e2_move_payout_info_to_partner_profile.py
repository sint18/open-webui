"""move payout info to partner profile"""

from alembic import op
import sqlalchemy as sa

revision = 'c8b9f0e5b6e2'
down_revision = 'a2f3d95bb0f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'partner_profile',
        sa.Column('payout_method', sa.String(), nullable=True),
        schema='affiliate'
    )
    op.add_column(
        'partner_profile',
        sa.Column('payout_details', sa.Text(), nullable=True),
        schema='affiliate'
    )


def downgrade():
    op.drop_column('partner_profile', 'payout_details', schema='affiliate')
    op.drop_column('partner_profile', 'payout_method', schema='affiliate')
