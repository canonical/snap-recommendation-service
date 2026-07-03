"""Add categories to snap

Revision ID: a1b2c3d4e5f6
Revises: b6616f20474f
Create Date: 2026-07-02 12:02:15.765109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'b6616f20474f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('snap', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categories', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('snap', schema=None) as batch_op:
        batch_op.drop_column('categories')
