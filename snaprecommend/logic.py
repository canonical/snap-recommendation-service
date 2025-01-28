from snaprecommend.models import Snap, SnapRecommendationScore
from snaprecommend import db


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
        .order_by(SnapRecommendationScore.score.desc())
        .limit(limit)
    ).all()

    return snaps
