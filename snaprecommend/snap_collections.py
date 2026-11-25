from snaprecommend.models import Snap, SnapCollection, SnapCollectionSnap
from snaprecommend import db
from sqlalchemy import func
from snaprecommend.utils import slugify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_snap_collection_by_id(collection_id: str) -> SnapCollection:
    """
    Returns a snap collection by its ID.
    """
    try:
        return db.session.query(SnapCollection).filter_by(id=collection_id).first()
    except Exception as e:
        logger.error(f"Error fetching snap collection {collection_id}: {e}")
        raise


def get_snap_collection_with_snaps(collection_id: str) -> SnapCollection:
    """
    Returns a snap collection by its ID with the snaps included.
    """
    try:
        snap_collection = (
            db.session.query(SnapCollection).filter_by(id=collection_id).first()
        )
        if snap_collection:
            snap_collection.snaps = (
                db.session.query(Snap)
                .join(SnapCollectionSnap)
                .filter_by(snap_collection_id=collection_id)
                .all()
            )
        return snap_collection
    except Exception as e:
        logger.error(
            f"Error fetching snap collection with snaps {collection_id}: {e}"
        )
        raise


def get_all_snap_collections_with_counts() -> list[SnapCollection]:
    """
    Returns all snap collections with the count of snaps.
    """
    try:
        snap_collections = (
            db.session.query(
                SnapCollection,
                func.count(SnapCollectionSnap.snap_id).label("snaps_count"),
            )
            .outerjoin(
                SnapCollectionSnap,
                SnapCollection.id == SnapCollectionSnap.snap_collection_id,
            )
            .group_by(SnapCollection.id)
            .all()
        )

        for snap_collection, snaps_count in snap_collections:
            snap_collection.snaps_count = snaps_count

        return [snap_collection for snap_collection, _ in snap_collections]
    except Exception as e:
        logger.error(f"Error fetching all snap collections: {e}")
        raise


def create_snap_collection(name: str, description: str = None):
    """
    Creates a new snap collection.
    """
    try:
        collection_id = slugify(name)
        if db.session.query(SnapCollection).filter_by(id=collection_id).first():
            raise ValueError(
                f"Snap collection with id '{collection_id}' already exists."
            )

        snap_collection = SnapCollection(
            id=collection_id, name=name, description=description
        )
        db.session.add(snap_collection)
        db.session.commit()
        return snap_collection
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating snap collection {name}: {e}")
        raise


def update_snap_collection(collection_id: str, name: str, description: str = None):
    """
    Updates a snap collection.
    """
    try:
        snap_collection = (
            db.session.query(SnapCollection).filter_by(id=collection_id).first()
        )
        if not snap_collection:
            raise ValueError(
                f"Snap collection with id '{collection_id}' not found."
            )

        snap_collection.name = name
        snap_collection.description = description
        db.session.commit()
        return snap_collection
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating snap collection {collection_id}: {e}")
        raise


def add_snap_to_snap_collection(collection_id: str, snap_id: str):
    """
    Adds a snap to a snap collection.
    """
    try:
        snap_collection_snap = SnapCollectionSnap(
            snap_collection_id=collection_id, snap_id=snap_id
        )
        db.session.add(snap_collection_snap)
        db.session.commit()
        return snap_collection_snap
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error adding snap {snap_id} to snap collection {collection_id}: {e}"
        )
        raise


def remove_snap_from_snap_collection(collection_id: str, snap_id: str):
    """
    Removes a snap from a snap collection.
    """
    try:
        snap_collection_snap = (
            db.session.query(SnapCollectionSnap)
            .filter_by(snap_collection_id=collection_id, snap_id=snap_id)
            .first()
        )
        if not snap_collection_snap:
            raise ValueError(
                f"Snap {snap_id} not found in snap collection {collection_id}."
            )

        db.session.delete(snap_collection_snap)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error removing snap {snap_id} from snap collection {collection_id}: {e}"
        )
        raise


def delete_snap_collection(collection_id: str):
    """
    Deletes a snap collection.
    """
    try:
        snap_collection = (
            db.session.query(SnapCollection).filter_by(id=collection_id).first()
        )
        if not snap_collection:
            raise ValueError(
                f"Snap collection with id '{collection_id}' not found."
            )

        db.session.delete(snap_collection)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting snap collection {collection_id}: {e}")
        raise
