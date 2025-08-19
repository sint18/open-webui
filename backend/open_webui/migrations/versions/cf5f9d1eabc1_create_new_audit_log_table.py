"""create new audit log table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

# revision identifiers, used by Alembic.
revision: str = 'cf5f9d1eabc1'
down_revision: Union[str, None] = 'ced652350042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('audit_log', schema='affiliate')
    op.execute("DROP TYPE IF EXISTS affiliate.audit_severity_enum")
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='affiliate'
    )


def downgrade() -> None:
    op.drop_table('audit_log', schema='affiliate')
    op.execute("CREATE TYPE affiliate.audit_severity_enum AS ENUM ('info','warning','critical')")
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
