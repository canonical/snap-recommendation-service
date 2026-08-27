"""Store pipeline steps without a PostgreSQL enum.

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-06 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


PIPELINE_STEPS_ENUM = postgresql.ENUM(
    "COLLECT",
    "FILTER",
    "EXTRA_FIELDS",
    "SCORE",
    name="pipelinesteps",
    create_type=False,
)


def upgrade():
    op.alter_column(
        "pipeline_step_log",
        "step",
        existing_type=PIPELINE_STEPS_ENUM,
        type_=sa.String(length=12),
        postgresql_using="step::text",
    )


def downgrade():
    op.alter_column(
        "pipeline_step_log",
        "step",
        existing_type=sa.String(length=12),
        type_=PIPELINE_STEPS_ENUM,
        postgresql_using="step::pipelinesteps",
    )
