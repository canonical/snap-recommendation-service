import flask
from snaprecommend.featuredsnaps.utils import get_featured_snaps
from snaprecommend.logic import record_featured_history
from snaprecommend.auth.session import publisher_gateway, device_gateway
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

    token = flask.session.get("developer_token")

    # currently_featured_snap is the list of featured snaps to be deleted
    currently_featured_snaps = []
    next = True
    while next:
        snaps = device_gateway.get_featured_snaps()
        currently_featured_snaps.extend(
            snaps.get("_embedded", {}).get("clickindex:package", [])
        )
        next = snaps.get("_links", {}).get("next", False)

    currently_featured_snap_ids = [
        snap["snap_id"] for snap in currently_featured_snaps
    ]

    def restore_previous_featured():
        publisher_gateway.update_featured_snaps(
            token, {"packages": currently_featured_snap_ids}
        )

    if len(currently_featured_snap_ids) > 0:
        delete_response = publisher_gateway.delete_featured_snaps(
            token, {"packages": currently_featured_snap_ids}
        )
        if delete_response.status_code != 201:
            response = {
                "success": False,
                "message": "An error occurred while deleting featured snaps",
            }
            return flask.make_response(response, 400)

    snap_ids = featured_snaps.split(",")
    payload = {"packages": snap_ids}
    update_response = publisher_gateway.update_featured_snaps(token, payload)

    if update_response.status_code in (401, 403):
        restore_previous_featured()

        return flask.make_response(
            {"success": False, "message": "Unauthorized to update featured snaps"},
            update_response.status_code,
        )
    if update_response.status_code != 201:
        restore_previous_featured()

        return flask.make_response(
            {
                "success": False,
                "message": f"Failed to update featured snaps (status {update_response.status_code}).",
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
        restore_previous_featured()
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
