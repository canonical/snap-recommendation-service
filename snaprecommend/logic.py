import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from snaprecommend.auth.session import device_gateway, publisher_gateway
from snaprecommend.models import (
    Snap,
    SnapRecommendationScore,
    RecommendationCategory,
    EditorialSlice,
    EditorialSliceSnap,
    FeaturedHistory,
    PipelineStepLog,
    PipelineSteps,
    Settings,
)
from snaprecommend import db

logger = logging.getLogger(__name__)

FEATURED_SELECTION_LOCK_KEY = "featured_selection_lock"
FEATURED_SELECTION_LOCK_TTL = timedelta(hours=6)


class FeaturedPublishError(Exception):
    """Base error raised when publishing the featured list to the store fails."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class FeaturedDeleteError(FeaturedPublishError):
    """Raised when deleting the currently featured snaps fails."""

    def __init__(self, status_code: int):
        super().__init__(
            f"Failed to delete current featured snaps (status {status_code}).",
            status_code=400,
        )
        self.upstream_status_code = status_code


class FeaturedUpdateError(FeaturedPublishError):
    """Raised when updating the store with the new featured list fails."""

    def __init__(self, status_code: int):
        resolved_status = status_code if status_code in (401, 403) else 500
        super().__init__(
            f"Failed to update featured snaps in store (status {status_code}).",
            status_code=resolved_status,
        )
        self.upstream_status_code = status_code


def get_snap_by_name(name: str) -> Snap | None:
    snap = db.session.query(Snap).filter_by(name=name).first()
    return snap


def get_category_top_snaps(category: str, limit: int = 50) -> list[Snap]:
    """
    Returns the top snaps for a given category.
    """

    snaps = (
        db.session.query(Snap)
        .join(
            SnapRecommendationScore,
            Snap.snap_id == SnapRecommendationScore.snap_id,
        )
        .filter(Snap.reaches_min_threshold.is_(True))
        .filter(Snap.excluded.is_(False))
        .filter(SnapRecommendationScore.category == category)
        .order_by(SnapRecommendationScore.score.desc())
        .limit(limit)
    ).all()

    return snaps


def exclude_snap(snap_id: str):
    snap = db.session.query(Snap).filter_by(snap_id=snap_id).first()
    if snap:
        snap.excluded = True
        db.session.commit()
        return True
    return False


def include_snap(snap_id: str):
    snap = db.session.query(Snap).filter_by(snap_id=snap_id).first()
    if snap:
        snap.excluded = False
        db.session.commit()
        return True
    return False


def get_all_categories() -> list[RecommendationCategory]:
    """
    Returns all available categories.
    """

    categories = db.session.query(RecommendationCategory).all()

    return categories


def get_excluded_snaps() -> list[Snap]:
    return db.session.query(Snap).filter(Snap.excluded.is_(True)).all()


def get_all_slices() -> list[EditorialSlice]:
    """
    Returns all editorial slices.
    """

    slices = db.session.query(EditorialSlice).all()

    return slices


def get_slice_snaps(slice: str) -> list[Snap]:
    """
    Returns the snaps for a given slice.
    """

    snaps = (
        db.session.query(Snap)
        .join(
            EditorialSliceSnap,
            Snap.snap_id == EditorialSliceSnap.snap_id,
        )
        .filter(EditorialSliceSnap.editorial_slice_id == slice)
    ).all()

    return snaps


def acquire_featured_selection_lock() -> bool:
    """Acquire a durable lock coordinating featured store/history updates."""
    now = datetime.now(timezone.utc)
    lock_row = db.session.query(Settings).filter(
        Settings.key == FEATURED_SELECTION_LOCK_KEY
    ).first()

    if lock_row:
        acquired_at = None
        try:
            acquired_at = datetime.fromisoformat(str(lock_row.value))
        except (TypeError, ValueError):
            acquired_at = None

        if acquired_at and acquired_at.tzinfo is None:
            acquired_at = acquired_at.replace(tzinfo=timezone.utc)

        if acquired_at and (now - acquired_at) <= FEATURED_SELECTION_LOCK_TTL:
            return False

        db.session.delete(lock_row)
        db.session.commit()

    db.session.add(Settings(key=FEATURED_SELECTION_LOCK_KEY, value=now.isoformat()))
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False


def release_featured_selection_lock() -> None:
    """Release the durable featured selection lock if it exists."""
    lock_row = db.session.query(Settings).filter(
        Settings.key == FEATURED_SELECTION_LOCK_KEY
    ).first()
    if lock_row:
        db.session.delete(lock_row)
        db.session.commit()


def get_current_featured_snap_ids() -> list:
    """Fetch the currently featured snap IDs from the store."""
    snaps = device_gateway.get_featured_snaps()
    currently_featured_snaps = snaps.get("_embedded", {}).get("clickindex:package", [])
    return [snap["snap_id"] for snap in currently_featured_snaps]


def publish_featured_snaps(token: str, new_snap_ids: list) -> list:
    """
    Replace the live featured list in the store with *new_snap_ids*.

    The store's update (PUT) endpoint does not replace the featured list, it
    only adds/updates entries, so the currently featured snaps must be
    deleted first. If the subsequent update fails, a best-effort restore of
    the previous list is attempted before raising.

    Returns the snap IDs that were featured before this call.
    Raises FeaturedDeleteError or FeaturedUpdateError on failure.
    """
    current_ids = get_current_featured_snap_ids()

    if current_ids:
        delete_resp = publisher_gateway.delete_featured_snaps(
            token, {"packages": current_ids}
        )
        if delete_resp.status_code != 201:
            raise FeaturedDeleteError(delete_resp.status_code)

    update_resp = publisher_gateway.update_featured_snaps(
        token, {"packages": new_snap_ids}
    )
    if update_resp.status_code not in (200, 201):
        rollback_featured_snaps(current_ids, token)
        raise FeaturedUpdateError(update_resp.status_code)

    return current_ids


def rollback_featured_snaps(previous_ids: list, token: str) -> None:
    """Best-effort restore of the store's featured list to *previous_ids*."""
    try:
        publisher_gateway.update_featured_snaps(token, {"packages": previous_ids})
    except Exception:
        logger.exception("Failed to roll back featured list in store.")


def record_featured_history(
    events: list[dict], is_manual: bool
) -> list[FeaturedHistory]:
    """
    Records featured-history events.
    """
    featured_at = datetime.now(timezone.utc)
    entries = [
        FeaturedHistory(
            snap_id=event["snap_id"],
            featured_at=featured_at,
            is_manual=is_manual,
            selection_reason=event.get("selection_reason"),
        )
        for event in events
    ]
    db.session.add_all(entries)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return entries


def get_latest_featured_events(snap_ids: list[str]) -> dict[str, dict]:
    """
    Returns the most recent featured event for each of the given snaps, keyed
    by snap_id. Snaps with no recorded history are absent from the result.
    """
    if not snap_ids:
        return {}

    ranked = (
        select(
            FeaturedHistory.snap_id,
            FeaturedHistory.featured_at,
            FeaturedHistory.is_manual,
            FeaturedHistory.selection_reason,
            func.row_number()
            .over(
                partition_by=FeaturedHistory.snap_id,
                order_by=(
                    FeaturedHistory.featured_at.desc(),
                    FeaturedHistory.id.desc(),
                ),
            )
            .label("rank"),
        )
        .where(FeaturedHistory.snap_id.in_(snap_ids))
        .subquery()
    )

    rows = db.session.execute(select(ranked).where(ranked.c.rank == 1)).all()

    return {
        row.snap_id: {
            "featured_at": row.featured_at.isoformat(),
            "is_manual": row.is_manual,
            "selection_reason": row.selection_reason,
        }
        for row in rows
    }


def add_pipeline_step_log(step_name: str, status: bool, message: str = ""):
    """
    Adds a log entry for a pipeline step.
    """

    log_entry = PipelineStepLog(
        step=step_name, success=status, message=message
    )
    db.session.add(log_entry)
    db.session.commit()


def get_most_recent_pipeline_step_logs():
    """
    Retrieve the most recent run information for each pipeline step.
    Groups by step and finds the last successful and failed runs for each.
    For status and message, uses the most recent run regardless of success/failure.

    Returns:
        list: A list of dictionaries containing information about pipeline steps
    """
    results = []

    # Get all unique steps from the enum
    all_steps = [step for step in PipelineSteps]

    for step in all_steps:

        most_recent = (
            PipelineStepLog.query.filter_by(step=step)
            .order_by(PipelineStepLog.created_at.desc())
            .first()
        )

        last_successful = (
            PipelineStepLog.query.filter_by(step=step, success=True)
            .order_by(PipelineStepLog.created_at.desc())
            .first()
        )

        last_failed = (
            PipelineStepLog.query.filter_by(step=step, success=False)
            .order_by(PipelineStepLog.created_at.desc())
            .first()
        )

        names = {
            PipelineSteps.SCORE: "Score",
            PipelineSteps.FILTER: "Filter",
            PipelineSteps.COLLECT: "Collect",
            PipelineSteps.EXTRA_FIELDS: "Extra fields",
            PipelineSteps.FEATURED: "Featured",
        }

        step_info = {
            "id": step.value,
            "name": names.get(step, step),
            "success": None,
            "last_successful_run": None,
            "last_failed_run": None,
            "message": None,
        }

        if most_recent:
            step_info["success"] = most_recent.success
            step_info["message"] = most_recent.message

        if last_successful:
            step_info["last_successful_run"] = last_successful.created_at

        if last_failed:
            step_info["last_failed_run"] = last_failed.created_at

        results.append(step_info)

    return results
