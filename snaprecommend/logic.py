from snaprecommend.models import (
    Snap,
    SnapRecommendationScore,
    RecommendationCategory,
)
from snaprecommend import db


def get_snap_by_name(name: str) -> Snap:
    snap = db.session.query(Snap).filter_by(name=name).first()
    print(name, snap)
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
