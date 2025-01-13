from flask import Blueprint
from snaprecommend.models import Snap, Scores
from snaprecommend import db

api_blueprint = Blueprint("api", __name__)


# fetch recommendations /popular
@api_blueprint.route("/popular")
def popular():
    snaps = get_top_snaps_by_field("popularity_score")

    return format_response(snaps)


@api_blueprint.route("/recent")
def recent():
    snaps = get_top_snaps_by_field("recency_score")

    return format_response(snaps)


@api_blueprint.route("/trending")
def trending():
    snaps = get_top_snaps_by_field("trending_score")

    return format_response(snaps)


def get_top_snaps_by_field(
    field: str, limit: int = 50, ascending: bool = False
) -> list[Snap]:
    """
    Returns the top snaps based on the given field
    """
    field = getattr(Scores, field)
    order = field.asc() if ascending else field.desc()

    snaps = db.session.query(Snap).join(Scores).order_by(order).limit(limit)

    return list(snaps)


def format_response(snaps: list[Snap]) -> list[dict]:
    return [
        {"snap_id": snap.snap_id, "name": snap.name, "rank": i + 1}
        for i, snap in enumerate(snaps)
    ]
