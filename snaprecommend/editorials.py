from snaprecommend.models import Snap, EditorialSlice, EditorialSliceSnap
from snaprecommend import db
from sqlalchemy import func
from snaprecommend.utils import slugify


def get_editorial_slice_by_id(slice_id: str) -> EditorialSlice:
    """
    Returns an editorial slice by its ID.
    """

    editorial_slice = (
        db.session.query(EditorialSlice).filter_by(id=slice_id).first()
    )

    return editorial_slice


def get_editorial_slice_with_snaps(slice_id: str) -> EditorialSlice:
    """
    Returns an editorial slice by its ID with the snaps included.
    """

    editorial_slice = (
        db.session.query(EditorialSlice).filter_by(id=slice_id).first()
    )

    if editorial_slice:
        editorial_slice.snaps = (
            db.session.query(Snap)
            .join(EditorialSliceSnap)
            .filter_by(editorial_slice_id=slice_id)
            .all()
        )

    return editorial_slice


def get_all_editorial_slices() -> list[EditorialSlice]:
    """
    Returns all editorial slices with the count of snaps.
    """

    editorial_slices = (
        db.session.query(
            EditorialSlice,
            func.count(EditorialSliceSnap.snap_id).label("snaps_count"),
        )
        .outerjoin(
            EditorialSliceSnap,
            EditorialSlice.id == EditorialSliceSnap.editorial_slice_id,
        )
        .group_by(EditorialSlice.id)
        .all()
    )

    for editorial_slice, snaps_count in editorial_slices:
        editorial_slice.snaps_count = snaps_count

    return [editorial_slice for editorial_slice, _ in editorial_slices]


def create_editorial_slice(name: str, description: str = None):
    """
    Creates a new editorial slice.
    """

    slice_id = slugify(name)

    existing_slice = (
        db.session.query(EditorialSlice).filter_by(id=slice_id).first()
    )

    if existing_slice:
        raise ValueError(
            f"Editorial slice with id '{slice_id}' already exists."
        )

    editorial_slice = EditorialSlice(
        id=slice_id,
        name=name,
        description=description,
    )

    db.session.add(editorial_slice)
    db.session.commit()
    return True


def add_snap_to_editorial_slice(
    slice_id: str,
    snap_id: str,
):
    """
    Adds a snap to an editorial slice.
    """

    editorial_slice_snap = EditorialSliceSnap(
        editorial_slice_id=slice_id,
        snap_id=snap_id,
    )

    db.session.add(editorial_slice_snap)
    db.session.commit()
    return True


def remove_snap_from_editorial_slice(
    slice_id: str,
    snap_id: str,
):
    """
    Removes a snap from an editorial slice.
    """

    editorial_slice_snap = (
        db.session.query(EditorialSliceSnap)
        .filter_by(editorial_slice_id=slice_id, snap_id=snap_id)
        .first()
    )

    if editorial_slice_snap:
        db.session.delete(editorial_slice_snap)
        db.session.commit()
        return True

    return False
