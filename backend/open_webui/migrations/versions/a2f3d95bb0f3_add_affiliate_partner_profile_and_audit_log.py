"""add affiliate partner profile and audit log"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a2f3d95bb0f3'
down_revision = '53f1f593d1c2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'partner_profile',
        sa.Column('partner_id', sa.String(), nullable=False),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', name='partner_status_enum', schema='affiliate'), nullable=False, server_default='active'),
        sa.Column('type', sa.Enum('individual', 'company', name='partner_type_enum', schema='affiliate'), nullable=False, server_default='individual'),
        sa.Column('terms', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['partner_id'], ['user.id']),
        sa.PrimaryKeyConstraint('partner_id'),
        schema='affiliate'
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'critical', name='audit_severity_enum', schema='affiliate'), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='affiliate'
    )

    op.add_column('coupon', sa.Column('expires_at', sa.BigInteger(), nullable=True), schema='affiliate')
    op.drop_column('coupon', 'discount_percent', schema='affiliate')
    op.create_foreign_key('fk_coupon_code_discount_code', 'coupon', 'discount_code', ['code'], ['code'], source_schema='affiliate')

    op.add_column('payout', sa.Column('reference', sa.String(), nullable=True, unique=True), schema='affiliate')


def downgrade():
    op.drop_column('payout', 'reference', schema='affiliate')

    op.drop_constraint('fk_coupon_code_discount_code', 'coupon', schema='affiliate', type_='foreignkey')
    op.add_column('coupon', sa.Column('discount_percent', sa.Numeric(), nullable=True), schema='affiliate')
    op.drop_column('coupon', 'expires_at', schema='affiliate')

    op.drop_table('audit_log', schema='affiliate')
    op.drop_table('partner_profile', schema='affiliate')
    op.execute('DROP TYPE affiliate.partner_type_enum')
    op.execute('DROP TYPE affiliate.partner_status_enum')
    op.execute('DROP TYPE affiliate.audit_severity_enum')
