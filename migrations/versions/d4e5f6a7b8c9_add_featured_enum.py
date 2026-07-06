"""Add FEATURED value to pipelinesteps enum

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-06 12:01:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE pipelinesteps ADD VALUE IF NOT EXISTS 'FEATURED'")


def downgrade():
    # PostgreSQL does not support removing enum values directly.
    # A full recreate is required if a rollback is needed.
    pass
