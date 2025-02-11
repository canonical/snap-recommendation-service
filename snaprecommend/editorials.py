from snaprecommend.models import Snap, EditorialSlice, EditorialSliceSnap
from snaprecommend import db
from sqlalchemy import func
from snaprecommend.utils import slugify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_editorial_slice_by_id(slice_id: str) -> EditorialSlice:
    """
    Returns an editorial slice by its ID.
    """
    try:
        return db.session.query(EditorialSlice).filter_by(id=slice_id).first()
    except Exception as e:
        logger.error(f"Error fetching editorial slice {slice_id}: {e}")
        raise


def get_editorial_slice_with_snaps(slice_id: str) -> EditorialSlice:
    """
    Returns an editorial slice by its ID with the snaps included.
    """
    try:
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
    except Exception as e:
        logger.error(
            f"Error fetching editorial slice with snaps {slice_id}: {e}"
        )
        raise


def get_all_editorial_slices() -> list[EditorialSlice]:
    """
    Returns all editorial slices with the count of snaps.
    """
    try:
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
    except Exception as e:
        logger.error(f"Error fetching all editorial slices: {e}")
        raise


def create_editorial_slice(name: str, description: str = None):
    """
    Creates a new editorial slice.
    """
    try:
        slice_id = slugify(name)
        if db.session.query(EditorialSlice).filter_by(id=slice_id).first():
            raise ValueError(
                f"Editorial slice with id '{slice_id}' already exists."
            )

        editorial_slice = EditorialSlice(
            id=slice_id, name=name, description=description
        )
        db.session.add(editorial_slice)
        db.session.commit()
        return editorial_slice
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating editorial slice {name}: {e}")
        raise


def update_editorial_slice(slice_id: str, name: str, description: str = None):
    """
    Updates an editorial slice.
    """
    try:
        editorial_slice = (
            db.session.query(EditorialSlice).filter_by(id=slice_id).first()
        )
        if not editorial_slice:
            raise ValueError(
                f"Editorial slice with id '{slice_id}' not found."
            )

        editorial_slice.name = name
        editorial_slice.description = description
        db.session.commit()
        return editorial_slice
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating editorial slice {slice_id}: {e}")
        raise


def add_snap_to_editorial_slice(slice_id: str, snap_id: str):
    """
    Adds a snap to an editorial slice.
    """
    try:
        editorial_slice_snap = EditorialSliceSnap(
            editorial_slice_id=slice_id, snap_id=snap_id
        )
        db.session.add(editorial_slice_snap)
        db.session.commit()
        return editorial_slice_snap
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error adding snap {snap_id} to editorial slice {slice_id}: {e}"
        )
        raise


def remove_snap_from_editorial_slice(slice_id: str, snap_id: str):
    """
    Removes a snap from an editorial slice.
    """
    try:
        editorial_slice_snap = (
            db.session.query(EditorialSliceSnap)
            .filter_by(editorial_slice_id=slice_id, snap_id=snap_id)
            .first()
        )
        if not editorial_slice_snap:
            raise ValueError(
                f"Snap {snap_id} not found in editorial slice {slice_id}."
            )

        db.session.delete(editorial_slice_snap)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error removing snap {snap_id} from editorial slice {slice_id}: {e}"
        )
        raise


def delete_editorial_slice(slice_id: str):
    """
    Deletes an editorial slice.
    """
    try:
        editorial_slice = (
            db.session.query(EditorialSlice).filter_by(id=slice_id).first()
        )
        if not editorial_slice:
            raise ValueError(
                f"Editorial slice with id '{slice_id}' not found."
            )

        db.session.delete(editorial_slice)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting editorial slice {slice_id}: {e}")
        raise
