"""add utm fields and active flag to affiliate links"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c59a1d734f9a'
down_revision = '23b91a37adcb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('link', sa.Column('utm_source', sa.String(), nullable=True), schema='affiliate')
    op.add_column('link', sa.Column('utm_medium', sa.String(), nullable=True), schema='affiliate')
    op.add_column('link', sa.Column('utm_campaign', sa.String(), nullable=True), schema='affiliate')
    op.add_column('link', sa.Column('utm_term', sa.String(), nullable=True), schema='affiliate')
    op.add_column('link', sa.Column('utm_content', sa.String(), nullable=True), schema='affiliate')
    op.add_column('link', sa.Column('active', sa.Boolean(), nullable=False, server_default='true'), schema='affiliate')


def downgrade():
    op.drop_column('link', 'active', schema='affiliate')
    op.drop_column('link', 'utm_content', schema='affiliate')
    op.drop_column('link', 'utm_term', schema='affiliate')
    op.drop_column('link', 'utm_campaign', schema='affiliate')
    op.drop_column('link', 'utm_medium', schema='affiliate')
    op.drop_column('link', 'utm_source', schema='affiliate')
