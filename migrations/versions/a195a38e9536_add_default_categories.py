"""Add default categories

Revision ID: a195a38e9536
Revises: 54528f756336
Create Date: 2025-01-26 09:00:56.255879

"""

from alembic import op
import sqlalchemy as sa
import json
import os


# revision identifiers, used by Alembic.
revision = "a195a38e9536"
down_revision = "54528f756336"
branch_labels = None
depends_on = None


def upgrade():
    try:
        path = os.path.join("migrations/data/categories.json")
        file = open(path, "r")
        categories = json.load(file)
        file.close()
        op.bulk_insert(
            sa.table(
                "recommendation_category",
                sa.column("id", sa.String),
                sa.column("name", sa.String),
                sa.column("description", sa.String),
            ),
            categories,
        )
    except Exception as e:
        print(f"Error loading categories: {e}")
        return


def downgrade():
    try:
        op.execute("DELETE FROM recommendation_category")
    except Exception as e:
        print(f"Error deleting categories: {e}")
    pass
