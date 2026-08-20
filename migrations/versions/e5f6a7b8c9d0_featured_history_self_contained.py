"""Make featured_history self-contained

Copies the snap details onto each row and drops the foreign key to 'snap',
so history persists.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-19 10:12:54.873583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None

FK_NAME = "featured_history_snap_id_fkey"


def _snap_foreign_key() -> str | None:
    """Return the name of the featured_history -> snap foreign key, if present."""
    inspector = sa.inspect(op.get_bind())
    for constraint in inspector.get_foreign_keys("featured_history"):
        if constraint["referred_table"] == "snap" and constraint["name"]:
            return constraint["name"]
    return None


def upgrade():
    op.add_column("featured_history", sa.Column("title", sa.String(), nullable=True))
    op.add_column("featured_history", sa.Column("name", sa.String(), nullable=True))
    op.add_column("featured_history", sa.Column("publisher", sa.String(), nullable=True))
    op.add_column("featured_history", sa.Column("icon", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE featured_history
        SET title = snap.title,
            name = snap.name,
            publisher = snap.publisher,
            icon = snap.icon
        FROM snap
        WHERE snap.snap_id = featured_history.snap_id
        """
    )

    foreign_key = _snap_foreign_key()
    if foreign_key:
        op.drop_constraint(foreign_key, "featured_history", type_="foreignkey")


def downgrade():
    op.execute("DELETE FROM featured_history WHERE snap_id NOT IN (SELECT snap_id FROM snap)")
    op.create_foreign_key(
        FK_NAME,
        "featured_history",
        "snap",
        ["snap_id"],
        ["snap_id"],
        ondelete="CASCADE",
    )
    op.drop_column("featured_history", "icon")
    op.drop_column("featured_history", "publisher")
    op.drop_column("featured_history", "name")
    op.drop_column("featured_history", "title")
