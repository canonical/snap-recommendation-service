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
    get_category_excluded_snaps,
    include_snap_in_category,
    get_snap_by_name,
)
from snaprecommend.sso import login_required
from snaprecommend.editorials import (
    get_all_editorial_slices,
    get_editorial_slice_with_snaps,
    create_editorial_slice,
    delete_editorial_slice,
    add_snap_to_editorial_slice,
    remove_snap_from_editorial_slice,
    update_editorial_slice,
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
@login_required
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
@login_required
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
@login_required
def popular_snaps():
    limit = flask.request.args.get("limit", 10)
    category = flask.request.args.get("category")

    popular_snaps = get_category_top_snaps(category, limit=limit)
    response = {
        "snaps": [serialize_snap(snap) for snap in popular_snaps],
    }

    return response


@api_blueprint.route("/excluded_snaps")
@login_required
def excluded_snaps():
    excluded_snaps = []
    for category in get_all_categories():
        snaps = get_category_excluded_snaps(category.id)
        excluded_snaps.append(
            {
                "category": {"name": category.name, "id": category.id},
                "snaps": [serialize_snap(snap) for snap in snaps],
            }
        )
    return flask.jsonify(excluded_snaps), 200


@api_blueprint.route("/include_snap", methods=["POST"])
@login_required
def include_snap():
    data = flask.request.get_json()
    snap_id = data.get("snap_id")
    category = data.get("category")
    if snap_id and category:
        include_snap_in_category(category, snap_id)
    return flask.jsonify({"status": "success"}), 200


def serialize_editorial_slice(editorial_slice):
    return {
        "name": editorial_slice.name,
        "id": editorial_slice.id,
        "description": editorial_slice.description,
        "snaps_count": editorial_slice.snaps_count,
    }


@api_blueprint.route("/editorial_slices")
@login_required
def editorial_slices():
    slices = get_all_editorial_slices()
    return flask.jsonify([serialize_editorial_slice(slice) for slice in slices],), 200


@api_blueprint.route("/editorial_slice", methods=["POST"])
@login_required
def create_slice():
    data = flask.request.get_json()
    name = data.get("name")
    description = data.get("description")

    try:
        create_editorial_slice(name, description)
    except ValueError:
        return flask.jsonify({"status": "failed", "error": "Slice cannot be created."}), 500

    return flask.jsonify({"status": "success"}), 200


@api_blueprint.route("/editorial_slice/<string:slice_id>")
@login_required
def editorial_slice(slice_id):
    slice = get_editorial_slice_with_snaps(slice_id)
    if not slice:
        return {"error": "Slice not found"}, 404

    return flask.jsonify({
        "id": slice.id,
        "name": slice.name,
        "description": slice.description,
        "snaps": [serialize_snap(snap) for snap in slice.snaps]
    }), 200


@api_blueprint.route(
    "/editorial_slice/<string:slice_id>", methods=["DELETE"]
)
@login_required
def delete_slice(slice_id):
    deleted = delete_editorial_slice(slice_id)
    if not deleted:
        return {"error": "Slice not found"}, 404
    return flask.jsonify({"status": "success"}), 200


@api_blueprint.route(
    "/editorial_slice/<string:slice_id>", methods=["POST"]
)
@login_required
def edit_slice(slice_id):
    data = flask.request.get_json()
    name = data.get("name")
    description = data.get("description")

    try:
        update_editorial_slice(slice_id, name, description)
    except ValueError:
        return flask.jsonify({"status": "failed", "error": "Slice cannot be created."}), 500

    return flask.jsonify({"status": "success"}), 200


@api_blueprint.route(
    "/editorial_slice/<string:slice_id>/snaps", methods=["POST"]
)
@login_required
def add_snap_to_slice(slice_id):
    data = flask.request.get_json()
    snap_name = data.get("name")
    slice = get_editorial_slice_with_snaps(slice_id)

    if not slice:
        return {"error": "Slice not found"}, 404

    snap = get_snap_by_name(snap_name)

    if snap:
        if snap.snap_id in [s.snap_id for s in slice.snaps]:
            return flask.jsonify({"status": "success"}), 200
        else:
            add_snap_to_editorial_slice(slice_id, snap.snap_id)
            return flask.jsonify({"status": "success"}), 200
    else:
        return {"error": "Snap not found"}, 404


@api_blueprint.route(
    "/editorial_slice/<string:slice_id>/remove_snap", methods=["POST"]
)
@login_required
def remove_snap_from_slice(slice_id):
    data = flask.request.get_json()
    snap_name = data.get("name")

    snap = get_snap_by_name(snap_name)

    if snap:
        remove_snap_from_editorial_slice(slice_id, snap.snap_id)
    else:
        return {"error": "Snap not found"}, 404
    return flask.jsonify({"status": "success"}), 200


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
