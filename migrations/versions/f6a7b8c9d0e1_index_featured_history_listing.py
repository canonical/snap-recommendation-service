"""Index featured_history for the unfiltered listing

The history endpoint orders by (featured_at, id) with no snap_id filter, which
the existing (snap_id, featured_at) index cannot serve — Postgres fell back to
a sequential scan plus a sort of the whole table.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-21 10:32:54.116843

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None

INDEX_NAME = "ix_featured_history_featured_at_id"


def upgrade():
    op.create_index(
        INDEX_NAME, "featured_history", ["featured_at", "id"]
    )


def downgrade():
    op.drop_index(INDEX_NAME, table_name="featured_history")
