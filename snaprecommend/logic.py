from snaprecommend.models import Snap, Scores
from snaprecommend import db


def get_top_snaps_by_field(
    field: str, limit: int = 50, ascending: bool = False
) -> list[Snap]:
    """
    Returns the top snaps based on the given field
    """
    field = getattr(Scores, field)
    order = field.asc() if ascending else field.desc()

    snaps = (
        db.session.query(Snap)
        .filter(Snap.reaches_min_threshold.is_(True))
        .join(Scores)
        .order_by(order)
        .limit(limit)
    )

    return list(snaps)
