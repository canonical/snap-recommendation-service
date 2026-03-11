"""remove score exclude columns

Revision ID: b2cb1a7be131
Revises: 1ec204a4d8f2
Create Date: 2026-03-11 12:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2cb1a7be131'
down_revision = '1ec204a4d8f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('snap_recommendation_score', schema=None) as batch_op:
        batch_op.drop_column('exclude')

    with op.batch_alter_table('snap_recommendation_score_history', schema=None) as batch_op:
        batch_op.drop_column('exclude')


def downgrade():
    with op.batch_alter_table('snap_recommendation_score_history', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('exclude', sa.Boolean(), nullable=False, server_default=sa.false())
        )

    with op.batch_alter_table('snap_recommendation_score', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('exclude', sa.Boolean(), nullable=False, server_default=sa.false())
        )
