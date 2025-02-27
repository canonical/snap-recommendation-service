"""initial

Revision ID: 7a6380990443
Revises: 
Create Date: 2025-01-07 14:27:41.368767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a6380990443'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('snap',
    sa.Column('snap_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('summary', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('icon', sa.String(), nullable=True),
    sa.Column('website', sa.String(), nullable=True),
    sa.Column('contact', sa.String(), nullable=True),
    sa.Column('publisher', sa.String(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('links', sa.JSON(), nullable=False),
    sa.Column('media', sa.JSON(), nullable=False),
    sa.Column('developer_validation', sa.String(), nullable=False),
    sa.Column('license', sa.String(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.Column('active_devices', sa.Integer(), nullable=False),
    sa.Column('reaches_min_threshold', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('snap_id')
    )
    op.create_table('scores',
    sa.Column('snap_id', sa.String(), nullable=False),
    sa.Column('popularity_score', sa.Float(), nullable=False),
    sa.Column('recency_score', sa.Float(), nullable=False),
    sa.Column('trending_score', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['snap_id'], ['snap.snap_id'],ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('snap_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scores')
    op.drop_table('snap')
    # ### end Alembic commands ###
