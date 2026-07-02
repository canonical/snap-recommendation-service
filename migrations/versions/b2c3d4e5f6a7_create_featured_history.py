"""Create featured_history table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-02 12:05:20.355084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "featured_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snap_id", sa.String(), nullable=False),
        sa.Column("featured_at", sa.DateTime(), nullable=False),
        sa.Column("is_manual", sa.Boolean(), nullable=False),
        sa.Column("selection_reason", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["snap_id"], ["snap.snap_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_featured_history_snap_id_featured_at",
        "featured_history",
        ["snap_id", "featured_at"],
    )


def downgrade():
    op.drop_index(
        "ix_featured_history_snap_id_featured_at",
        table_name="featured_history",
    )
    op.drop_table("featured_history")
