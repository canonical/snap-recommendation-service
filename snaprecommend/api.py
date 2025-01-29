from flask import Blueprint
from snaprecommend.models import Snap, RecommendationCategory
from snaprecommend.logic import get_category_top_snaps

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/categories")
def categories():
    categories = RecommendationCategory.query.all()

    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
        }
        for category in categories
    ]


@api_blueprint.route("/category/<string:id>")
def category(id: str):
    category = RecommendationCategory.query.filter_by(id=id).first()

    if category is None:
        return {"error": "Category not found"}, 404

    snaps = get_category_top_snaps(id)

    return format_response(snaps)


def format_response(snaps: list[Snap]) -> list[dict]:
    return [
        {"snap_id": snap.snap_id, "name": snap.name, "rank": i + 1}
        for i, snap in enumerate(snaps)
    ]
