import threading
from datetime import datetime, timedelta, timezone

import flask
from flask import Blueprint

from collector.main import (
    calculate_scores,
    collect_initial_snap_data,
    fetch_extra_fields,
    filter_snaps_meeting_minimum_criteria,
)
from snaprecommend import db
from snaprecommend.auth.decorators import admin_required, login_required
from snaprecommend.editorials import (
    add_snap_to_editorial_slice,
    create_editorial_slice,
    delete_editorial_slice,
    get_all_editorial_slices,
    get_editorial_slice_with_snaps,
    remove_snap_from_editorial_slice,
    update_editorial_slice,
)
from snaprecommend.logic import (
    exclude_snap as exclude_snap_globally,
)
from snaprecommend.logic import (
    get_all_categories,
    get_all_slices,
    get_category_top_snaps,
    get_excluded_snaps,
    get_most_recent_pipeline_step_logs,
    get_slice_snaps,
    get_snap_by_name,
)
from snaprecommend.logic import (
    include_snap as include_snap_globally,
)
from snaprecommend.models import (
    EditorialSlice,
    PipelineSteps,
    RecommendationCategory,
    Settings,
    Snap,
)
from snaprecommend.settings import get_setting, get_settings_by_keys
from snaprecommend.utils import api_response

api_blueprint = Blueprint("api", __name__)

_FEATURED_SETTINGS_INT_BOUNDS = {
    "featured_candidate_pool_size": (3, 1000),
    "featured_category_cap": (1, 100),
    "featured_recency_days": (1, 3650),
    "featured_history_window_days": (1, 3650),
}
_FEATURED_SETTINGS_FLOAT_BOUNDS = {
    "featured_min_rating": (0.0, 5.0),
}


@api_blueprint.route("/stats")
def stats():
    last_24_hours = datetime.now(timezone.utc) - timedelta(hours=24)

    total_tracked = Snap.query.count()
    new_today = Snap.query.filter(
        Snap.date_published >= last_24_hours
    ).count()
    updated_today = Snap.query.filter(
        Snap.last_updated >= last_24_hours,
        Snap.date_published < last_24_hours,
    ).count()

    return flask.jsonify({
        "total_tracked": total_tracked,
        "new_today": new_today,
        "updated_today": updated_today,
    }), 200


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


@api_blueprint.route("/excluded_snaps")
@login_required
def excluded_snaps():
    globally_excluded_snaps = get_excluded_snaps()
    return flask.jsonify(
        [serialize_snap(snap) for snap in globally_excluded_snaps]
    ), 200


@api_blueprint.route("/include_snap", methods=["POST"])
@login_required
def include_snap():
    data = flask.request.get_json()
    snap_id = data.get("snap_id")
    if snap_id:
        include_snap_globally(snap_id)
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


@api_blueprint.route("/settings")
@login_required
def get_collector_info():
    pipeline_steps = get_most_recent_pipeline_step_logs()

    last_updated = get_setting("last_updated")

    if last_updated.value:
        last_updated = datetime.fromisoformat(last_updated.value)

    return flask.jsonify({
        "pipeline_steps": pipeline_steps,
        "last_updated": last_updated,
    }), 200


@api_blueprint.route("/run_pipeline_step", methods=["POST"])
@login_required
def run_pipeline_step():
    data = flask.request.get_json()
    step_name = data.get("step_name")
    if not step_name:
        return {"error": "Step name is required"}, 400

    steps_map = {
        PipelineSteps.COLLECT.value: collect_initial_snap_data,
        PipelineSteps.FILTER.value: filter_snaps_meeting_minimum_criteria,
        PipelineSteps.EXTRA_FIELDS.value: fetch_extra_fields,
        PipelineSteps.SCORE.value: calculate_scores,
    }

    if step_name not in steps_map:
        return {"error": "Invalid step name"}, 400

    step_function = steps_map[step_name]

    def run_step(app_context):
        app_context.push()
        try:
            step_function()
        finally:
            app_context.pop()

    threading.Thread(
        target=run_step,
        args=(flask.current_app.app_context(),),
    ).start()

    # TODO: tmp fix until we add "in_progress" to steps
    return {
        "status": "success",
        "message": f"Pipeline step '{step_name}' started, please don't trigger again until last run time is updated",
    }, 200


@api_blueprint.route("/featured/select", methods=["POST"])
@login_required
@admin_required
def trigger_featured_selection():
    """
    Trigger an automated featured snap selection immediately. The publisher
    token used to update the store list is always resolved from the
    environment (see collector.featured_selector.select_featured_snaps).
    Runs in a background thread to avoid blocking the request.
    """
    from collector.featured_selector import select_featured_snaps
    from collector.main import featured_selection_due

    payload = flask.request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return flask.jsonify({
            "status": "error",
            "message": "Request body must be a JSON object.",
        }), 400

    unknown = set(payload.keys()) - {"force"}
    if unknown:
        return flask.jsonify({
            "status": "error",
            "message": f"Unknown field(s): {', '.join(sorted(unknown))}",
        }), 400

    force = payload.get("force", False)
    if "force" in payload and not isinstance(force, bool):
        return flask.jsonify({
            "status": "error",
            "message": "'force' must be a JSON boolean.",
        }), 400

    if not force and not featured_selection_due():
        return flask.jsonify({
            "status": "skipped",
            "message": (
                "Featured selection is not due yet according to its schedule. "
                "Pass {\"force\": true} to override."
            ),
        }), 200

    app_ctx = flask.current_app.app_context()

    def _run(ctx):
        ctx.push()
        try:
            select_featured_snaps()
        finally:
            ctx.pop()

    threading.Thread(target=_run, args=(app_ctx,), daemon=True).start()

    return flask.jsonify({
        "status": "success",
        "message": "Automated featured snap selection started.",
    }), 200


@api_blueprint.route("/featured/settings", methods=["GET"])
@login_required
def get_featured_settings():
    """Return the current featured-selection configuration."""
    keys = [
        "featured_candidate_pool_size",
        "featured_category_cap",
        "featured_min_rating",
        "featured_recency_days",
        "featured_history_window_days",
        "featured_last_updated",
    ]
    settings = get_settings_by_keys(keys)
    result = {key: s.value if s else None for key, s in settings.items()}

    from collector.main import featured_next_run, featured_schedule_description

    result["featured_schedule"] = featured_schedule_description()
    result["featured_next_run"] = featured_next_run().isoformat()

    return flask.jsonify(result), 200


@api_blueprint.route("/featured/settings", methods=["PATCH"])
@login_required
@admin_required
def update_featured_settings():
    """
    Update one or more featured-selection settings.
    Only the known configuration keys are accepted.
    """
    allowed_keys = {
        "featured_candidate_pool_size",
        "featured_category_cap",
        "featured_min_rating",
        "featured_recency_days",
        "featured_history_window_days",
    }
    data = flask.request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return flask.jsonify({
            "status": "error",
            "message": "Request body must be a JSON object.",
        }), 400

    unknown = set(data.keys()) - allowed_keys
    if unknown:
        return flask.jsonify({
            "status": "error",
            "message": f"Unknown setting(s): {', '.join(sorted(unknown))}",
        }), 400

    validated: dict = {}
    for key, value in data.items():
        if key in _FEATURED_SETTINGS_INT_BOUNDS:
            if isinstance(value, bool) or not isinstance(value, int):
                return flask.jsonify({
                    "status": "error",
                    "message": f"'{key}' must be an integer.",
                }), 400

            min_value, max_value = _FEATURED_SETTINGS_INT_BOUNDS[key]
            if value < min_value or value > max_value:
                return flask.jsonify({
                    "status": "error",
                    "message": (
                        f"'{key}' must be between {min_value} and {max_value}."
                    ),
                }), 400

            validated[key] = value
            continue

        if key in _FEATURED_SETTINGS_FLOAT_BOUNDS:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return flask.jsonify({
                    "status": "error",
                    "message": f"'{key}' must be a number.",
                }), 400

            min_value, max_value = _FEATURED_SETTINGS_FLOAT_BOUNDS[key]
            value = float(value)
            if value < min_value or value > max_value:
                return flask.jsonify({
                    "status": "error",
                    "message": (
                        f"'{key}' must be between {min_value} and {max_value}."
                    ),
                }), 400

            validated[key] = value

    if validated:
        existing_rows = Settings.query.filter(Settings.key.in_(validated.keys())).all()
        by_key = {row.key: row for row in existing_rows}

        for key, value in validated.items():
            row = by_key.get(key)
            if row:
                row.value = value
            else:
                db.session.add(Settings(key=key, value=value))

        db.session.commit()

    return flask.jsonify({"status": "success"}), 200


@api_blueprint.route("/exclude_snap", methods=["POST"])
@login_required
def exclude_snap():
    data = flask.request.get_json()
    snap_id = data.get("snap_id")
    if snap_id:
        exclude_snap_globally(snap_id)
    return flask.jsonify({"status": "success"}), 200


@api_blueprint.route("/recently-updated", methods=["GET"])
def recenty_updated():
    page = int(flask.request.args.get("page", 1))
    size = int(flask.request.args.get("size", 10))

    snaps = Snap.query.order_by(Snap.last_updated.desc()).paginate(page=page, per_page=size, max_per_page=50, error_out=False).items
    return flask.jsonify({
        "page": page,
        "size": min(size, 50),
        "snaps": [serialize_snap(snap) for snap in snaps],
    }), 200


@api_blueprint.route("/collected_snaps/search", methods=["GET"])
@login_required
def search_collected_snaps():
    """
    Search through collected snaps in the database.
    Returns results in a format compatible with the store API.
    """
    query = flask.request.args.get("q", "")

    if not query or len(query) < 3:
        return api_response({"packages": []})

    search_pattern = f"%{query}%"
    snaps = Snap.query.filter(
        (Snap.title.ilike(search_pattern)) |
        (Snap.name.ilike(search_pattern)) |
        (Snap.summary.ilike(search_pattern))
    ).limit(15).all()

    # Format results to match the store API format
    packages = [
        {
            "snap_id": snap.snap_id,
            "package": {
                "name": snap.name,
                "display_name": snap.title,
                "description": snap.summary,
                "icon_url": snap.icon,
                "type": "app",
                "platforms": []
            },
            "publisher": {
                "display_name": snap.publisher,
                "name": snap.publisher,
                "validation": snap.developer_validation
            },
            "categories": []
        }
        for snap in snaps
    ]

    return api_response({"packages": packages})


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
