from flask import Blueprint
from snaprecommend.models import Snap
from snaprecommend.logic import get_top_snaps_by_field

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


def format_response(snaps: list[Snap]) -> list[dict]:
    return [
        {"snap_id": snap.snap_id, "name": snap.name, "rank": i + 1}
        for i, snap in enumerate(snaps)
    ]
