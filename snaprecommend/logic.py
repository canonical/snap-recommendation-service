from snaprecommend.models import (
    Snap,
    SnapRecommendationScore,
    RecommendationCategory,
    EditorialSlice,
    EditorialSliceSnap,
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
        .filter(SnapRecommendationScore.category == category)
        .filter(SnapRecommendationScore.exclude.is_(False))
        .order_by(SnapRecommendationScore.score.desc())
        .limit(limit)
    ).all()

    return snaps


def exclude_snap_from_category(category: str, snap_id: str):
    """
    Excludes a snap from a given category.
    """

    snap_score = (
        db.session.query(SnapRecommendationScore)
        .filter_by(snap_id=snap_id, category=category)
        .first()
    )

    if snap_score:
        snap_score.exclude = True
        db.session.commit()
        return True

    return False


def include_snap_in_category(category: str, snap_id: str):
    """
    Includes a snap in a given category.
    """

    snap_score = (
        db.session.query(SnapRecommendationScore)
        .filter_by(snap_id=snap_id, category=category)
        .first()
    )

    if snap_score:
        snap_score.exclude = False
        db.session.commit()
        return True

    return False


def get_all_categories() -> list[RecommendationCategory]:
    """
    Returns all available categories.
    """

    categories = db.session.query(RecommendationCategory).all()

    return categories


def get_category_excluded_snaps(category: str) -> list[Snap]:
    """
    Returns the excluded snaps for a given category.
    """

    snaps = (
        db.session.query(Snap)
        .join(
            SnapRecommendationScore,
            Snap.snap_id == SnapRecommendationScore.snap_id,
        )
        .filter(SnapRecommendationScore.category == category)
        .filter(SnapRecommendationScore.exclude.is_(True))
        .order_by(SnapRecommendationScore.score.desc())
    ).all()

    return snaps


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
