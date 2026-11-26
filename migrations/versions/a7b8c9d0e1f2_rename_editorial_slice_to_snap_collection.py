"""rename editorial_slice tables to snap_collection

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def _rebuild_constraints(parent: str, child: str, fk_column: str) -> None:
    """Drop and recreate the constraints of parent/child using default names."""
    inspector = sa.inspect(op.get_bind())

    for constraint in inspector.get_foreign_keys(child):
        if constraint["name"]:
            op.drop_constraint(constraint["name"], child, type_="foreignkey")
    for table in (child, parent):
        pk_name = inspector.get_pk_constraint(table)["name"]
        if pk_name:
            op.drop_constraint(pk_name, table, type_="primary")

    op.create_primary_key(f"{parent}_pkey", parent, ["id"])
    op.create_primary_key(f"{child}_pkey", child, [fk_column, "snap_id"])
    op.create_foreign_key(
        f"{child}_{fk_column}_fkey",
        child,
        parent,
        [fk_column],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        f"{child}_snap_id_fkey",
        child,
        "snap",
        ["snap_id"],
        ["snap_id"],
        ondelete="CASCADE",
    )


def upgrade():
    op.rename_table('editorial_slice', 'snap_collection')
    op.rename_table('editorial_slice_snap', 'snap_collection_snap')
    with op.batch_alter_table('snap_collection_snap', schema=None) as batch_op:
        batch_op.alter_column('editorial_slice_id', new_column_name='snap_collection_id')
    _rebuild_constraints('snap_collection', 'snap_collection_snap', 'snap_collection_id')


def downgrade():
    with op.batch_alter_table('snap_collection_snap', schema=None) as batch_op:
        batch_op.alter_column('snap_collection_id', new_column_name='editorial_slice_id')
    op.rename_table('snap_collection_snap', 'editorial_slice_snap')
    op.rename_table('snap_collection', 'editorial_slice')
    _rebuild_constraints('editorial_slice', 'editorial_slice_snap', 'editorial_slice_id')
