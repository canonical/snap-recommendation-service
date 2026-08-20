import flask
from snaprecommend.featuredsnaps.utils import get_featured_snaps
from snaprecommend.logic import (
    FeaturedDeleteError,
    FeaturedUpdateError,
    acquire_featured_selection_lock,
    get_all_featured_history,
    publish_featured_snaps,
    record_featured_history,
    release_featured_selection_lock,
    rollback_featured_snaps,
)
from snaprecommend.auth.decorators import (
    login_required,
    exchange_required,
    admin_required,
)

featured_blueprint = flask.Blueprint("featured", __name__)


@featured_blueprint.route("/")
def featured_snaps():
    featured = get_featured_snaps()
    return flask.jsonify(featured), 200


DEFAULT_HISTORY_LIMIT = 200
MAX_HISTORY_LIMIT = 1000


@featured_blueprint.route("/history")
@login_required
@admin_required
def featured_history():
    limit = flask.request.args.get(
        "limit", default=DEFAULT_HISTORY_LIMIT, type=int
    )
    if limit is None or limit < 1:
        limit = DEFAULT_HISTORY_LIMIT
    limit = min(limit, MAX_HISTORY_LIMIT)

    return flask.jsonify(get_all_featured_history(limit)), 200


@featured_blueprint.route("/", methods=["POST"])
@exchange_required
@login_required
@admin_required
def post_featured_snaps():
    featured_snaps = flask.request.form.get("snaps")
    if not featured_snaps:
        response = {
            "success": False,
            "message": "Snaps cannot be empty",
        }
        return flask.make_response(response, 500)

    if not acquire_featured_selection_lock():
        response = {
            "success": False,
            "message": "Featured update already in progress. Please retry.",
        }
        return flask.make_response(response, 409)

    try:
        token = flask.session.get("developer_token")

        snap_ids = featured_snaps.split(",")

        try:
            previous_ids = publish_featured_snaps(token, snap_ids)
        except FeaturedDeleteError:
            response = {
                "success": False,
                "message": "An error occurred while deleting featured snaps",
            }
            return flask.make_response(response, 400)
        except FeaturedUpdateError as exc:
            if exc.upstream_status_code in (401, 403):
                return flask.make_response(
                    {"success": False, "message": "Unauthorized to update featured snaps"},
                    exc.upstream_status_code,
                )
            return flask.make_response(
                {
                    "success": False,
                    "message": f"Failed to update featured snaps (status {exc.upstream_status_code}).",
                },
                500,
            )

        # Record the manual edit in the shared featured history.
        publisher = flask.session.get("publisher", {})
        reason = {
            "actor": publisher.get("email"),
            "nickname": publisher.get("nickname"),
        }
        events = [
            {"snap_id": snap_id, "selection_reason": reason}
            for snap_id in snap_ids
        ]
        try:
            record_featured_history(events, is_manual=True)
        except Exception:
            # Keep the store and history all-or-nothing: revert the live list to
            # what it was before this edit so neither side sticks.
            rollback_featured_snaps(previous_ids, token)
            flask.current_app.logger.exception(
                "Failed to record featured history; reverted featured snaps to previous state"
            )
            return flask.make_response(
                {
                    "success": False,
                    "message": "Featured update rolled back due to an internal error.",
                },
                500,
            )

        return flask.make_response({"success": True}, 200)
    finally:
        release_featured_selection_lock()
