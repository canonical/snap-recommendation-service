from flask import Blueprint
import flask
from snaprecommend.models import (
    Snap,
    RecommendationCategory,
    EditorialSlice,
)
from snaprecommend.logic import (
    get_category_top_snaps,
    get_slice_snaps,
    get_all_categories,
    get_all_slices,
)

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/categories")
def categories():
    categories = get_all_categories()

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


@api_blueprint.route("/slices")
def slices():
    slices = get_all_slices()

    return [
        {
            "id": slice.id,
            "name": slice.name,
            "description": slice.description,
        }
        for slice in slices
    ]


@api_blueprint.route("/slice/<string:id>")
def slice(id: str):
    slice = EditorialSlice.query.filter_by(id=id).first()

    if slice is None:
        return {"error": "Slice not found"}, 404

    snaps = get_slice_snaps(id)

    response = {
        "slice": {
            "id": slice.id,
            "name": slice.name,
            "description": slice.description,
        },
        "snaps": [serialize_snap(snap) for snap in snaps],
    }

    return response


@api_blueprint.route("/snaps")
def popular_snaps():
    limit = flask.request.args.get("limit", 10)
    category = flask.request.args.get("category")

    popular_snaps = get_category_top_snaps(category, limit=limit)
    response = {
        "snaps": [serialize_snap(snap) for snap in popular_snaps],
    }

    return response


def format_response(snaps: list[Snap]) -> list[dict]:

    return [
        {
            "snap_id": snap.snap_id,
            "rank": i + 1,
            "details": serialize_snap(snap),
        }
        for i, snap in enumerate(snaps)
    ]


def serialize_snap(snap: Snap) -> dict:
    return {
        "snap_id": snap.snap_id,
        "title": snap.title,
        "name": snap.name,
        "version": snap.version,
        "summary": snap.summary,
        "description": snap.description,
        "icon": snap.icon,
        "website": snap.website,
        "contact": snap.contact,
        "publisher": snap.publisher,
        "revision": snap.revision,
        "links": snap.links,
        "media": snap.media,
        "developer_validation": snap.developer_validation,
        "license": snap.license,
        "last_updated": snap.last_updated,
    }
