"""add global snap exclusion

Revision ID: 1ec204a4d8f2
Revises: c1096f7c4215
Create Date: 2026-03-11 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ec204a4d8f2'
down_revision = 'c1096f7c4215'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('snap', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('excluded', sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    with op.batch_alter_table('snap', schema=None) as batch_op:
        batch_op.drop_column('excluded')
