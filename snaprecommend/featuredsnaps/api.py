import flask
from snaprecommend.featuredsnaps.utils import get_featured_snaps
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
    # ['wShl4osatuO4sXk2TfzrxE6hZF0biJhS', 'bIb4p4yWWjyZdo2EU64whkZhw9QYYsMH', 'hHiqKR3Bgg6i591bUdkHAzscVywZbpQP', 'wVB1RfBgsZY8dmVifSFeMkTE6UN41osI', 'kvAx1DJUbiqow1LgLfW5OzjksfqUEcqJ', 'ZtF4mLp5Bededu3S65ocO6HfGXCtcvZ9', '6JBjLwyVchga4cOSDqhWJd9NgQfrTYam', 'lfWUNpR7PrPGsDfuxIhVxbj0wZHoH7bK', 'wZo5sef6NuUKCW6DP83fJ6zIZyd5R1sA', 'G9GFr0OFxXrWLDuyfXXD07GFG8UflpJN', 'SfUqQ280Y4bJ0k64qtBKTTXq5ml46tvQ', 'wtlQQaUNASoWxqfxRflcRjU3au6cQ3X0', 'roFhaRzMw8ted6zNEL8NQnNrkFdIHnHv', 'qYBYNvfcQaSWRQAhY89lwrtniZeZMWRH', 'DtXxirDGfOc8LeUJVENXGTir4Oq0F7Ts', 'JbSwFezsVhBG8EpYeNqD4HX31U5WIzdY']
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

    if len(currently_featured_snap_ids) > 0:
        delete_response = publisher_gateway.delete_featured_snaps(
            token, {"packages": currently_featured_snap_ids}
        )

        # Print status code
        print("Status Code:", delete_response.status_code)

        # Print response body
        print("Response Body:", delete_response.text)
        if delete_response.status_code != 201:
            response = {
                "success": False,
                "message": "An error occurred while deleting featured snaps",
            }
            return flask.make_response(response, 400)

    snap_ids = featured_snaps.split(",")
    payload = {"packages": snap_ids}
    update_response = publisher_gateway.update_featured_snaps(token, payload)
   # Print status code
    print("Status Code:", update_response.status_code)

    # Print response body
    print("Response Body:", update_response.text)
    if update_response.status_code in (401, 403):
        publisher_gateway.update_featured_snaps(token, {"packages": currently_featured_snap_ids})

        return flask.make_response(
            {"success": False, "message": "Unauthorized to update featured snaps"},
            update_response.status_code,
        )
    if update_response.status_code != 201:
        publisher_gateway.update_featured_snaps(token, {"packages": currently_featured_snap_ids})

        return flask.make_response(
            {
                "success": False,
                "message": f"Failed to update featured snaps (status {update_response.status_code})",
            },
            500,
        )

    return flask.make_response({"success": True}, 200)
