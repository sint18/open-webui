"""create affiliate schema and tables"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = 'f7e8308eaa9c'
down_revision: Union[str, None] = 'ced652350042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enumerations
attr_via_enum = sa.Enum('link', 'coupon', 'manual', name='attr_via_enum', schema='affiliate')
commission_type_enum = sa.Enum('sale', 'lead', 'bonus', name='commission_type_enum', schema='affiliate')
commission_status_enum = sa.Enum('pending', 'approved', 'rejected', 'paid', name='commission_status_enum', schema='affiliate')
application_status_enum = sa.Enum('pending', 'approved', 'rejected', name='application_status_enum', schema='affiliate')
payout_status_enum = sa.Enum('pending','approved','paid','rejected', name='payout_status_enum', schema='affiliate')

def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS affiliate')

    op.create_table(
        'application',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('status', application_status_enum, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'link',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'coupon',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('discount_percent', sa.Numeric(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'click',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('link_id', sa.String(), nullable=True),
        sa.Column('coupon_id', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate',
    )

    op.create_table(
        'attribution',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('click_id', sa.BigInteger(), nullable=False),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('attr_via', attr_via_enum, nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['click_id'], ['affiliate.click.id']),
        schema='affiliate'
    )

    op.create_table(
        'order_attribution',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('attribution_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['attribution_id'], ['affiliate.attribution.id']),
        schema='affiliate'
    )

    op.create_table(
        'commission',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('type', commission_type_enum, nullable=False),
        sa.Column('status', commission_status_enum, nullable=False, server_default='pending'),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'commission_adjustment',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('commission_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['commission_id'], ['affiliate.commission.id']),
        schema='affiliate'
    )

    op.create_table(
        'payout',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('total_amount', sa.Numeric(), nullable=False),
        sa.Column('status', payout_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'payout_item',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('payout_id', sa.String(), nullable=False),
        sa.Column('commission_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['payout_id'], ['affiliate.payout.id']),
        sa.ForeignKeyConstraint(['commission_id'], ['affiliate.commission.id']),
        schema='affiliate'
    )

    op.create_table(
        'fraud_flag',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('flag_type', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        schema='affiliate'
    )

    op.create_table(
        'outbox_event',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('processed_at', sa.BigInteger(), nullable=True),
        schema='affiliate'
    )

    # Example view for reporting
    op.execute(
        """
        CREATE VIEW affiliate.partner_commission_totals AS
        SELECT partner_id, SUM(amount) AS total_amount
        FROM affiliate.commission
        GROUP BY partner_id
        """
    )


def downgrade() -> None:
    op.execute('DROP VIEW IF EXISTS affiliate.partner_commission_totals')

    op.drop_table('payout_item', schema='affiliate')
    op.drop_table('payout', schema='affiliate')
    op.drop_table('commission_adjustment', schema='affiliate')
    op.drop_table('commission', schema='affiliate')
    op.drop_table('order_attribution', schema='affiliate')
    op.drop_table('attribution', schema='affiliate')
    op.execute('DROP TABLE IF EXISTS affiliate.click_default')
    op.drop_table('click', schema='affiliate')
    op.drop_table('coupon', schema='affiliate')
    op.drop_table('link', schema='affiliate')
    op.drop_table('application', schema='affiliate')
    op.drop_table('fraud_flag', schema='affiliate')
    op.drop_table('outbox_event', schema='affiliate')

    commission_status_enum.drop(op.get_bind(), checkfirst=True)
    commission_type_enum.drop(op.get_bind(), checkfirst=True)
    attr_via_enum.drop(op.get_bind(), checkfirst=True)

    op.execute('DROP SCHEMA IF EXISTS affiliate')
