from datetime import datetime
from snaprecommend.models import (
    Snap,
    SnapRecommendationScore,
    RecommendationCategory,
    EditorialSlice,
    EditorialSliceSnap,
    FeaturedHistory,
    PipelineStepLog,
    PipelineSteps,
)
from snaprecommend import db


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


def record_featured_history(
    events: list[dict], is_manual: bool
) -> list[FeaturedHistory]:
    """
    Records featured-history events.
    """
    featured_at = datetime.utcnow()
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


def get_featured_history(snap_ids: list[str]) -> dict[str, list[dict]]:
    """
    Returns featured history for the given snaps, grouped by snap_id with each
    snap's events ordered newest-first.
    """
    if not snap_ids:
        return {}

    rows = (
        db.session.query(FeaturedHistory)
        .filter(FeaturedHistory.snap_id.in_(snap_ids))
        .order_by(
            FeaturedHistory.featured_at.desc(),
            FeaturedHistory.id.desc(),
        )
        .all()
    )

    history: dict[str, list[dict]] = {}
    for row in rows:
        history.setdefault(row.snap_id, []).append(
            {
                "featured_at": row.featured_at.isoformat(),
                "is_manual": row.is_manual,
                "selection_reason": row.selection_reason,
            }
        )

    return history


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
