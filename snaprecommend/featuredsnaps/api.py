import flask
import os
from snaprecommend.featuredsnaps.utils import get_fetaured_snaps
from snaprecommend.auth.session import device_gateway, publisher_gateway, dashboard, api_session, api_publisher_session
from snaprecommend.auth.decorators import login_required, exchange_required, admin_required
from config import MACAROON_ENV_PATH
import requests

featured_blueprint = flask.Blueprint("featured", __name__)
MACAROON = "AgEQYXBpLnNuYXBjcmFmdC5pbwImAwoQdaHnNfcOsE97M4aht5DANhIBMBoOCgVsb2dpbhIFbG9naW4AAid0aW1lLWJlZm9yZSAyMDI1LTExLTEzVDIxOjAwOjQzLjAwMDIzNFoAAiZ0aW1lLXNpbmNlIDIwMjUtMDktMTdUMDU6NDg6MTYuNTI1Mjk1WgACL3Nlc3Npb24taWQgOTkyY2NiMzktZTFhOS0xOWUwLTU3NDEtNGQ1ODQ5MTE3YzU1AAI5ZGVjbGFyZWQgdXNlcmlkIHVzc286aHR0cHM6Ly9sb2dpbi51YnVudHUuY29tLytpZC9OZXM3ZEVLAAIvZXh0cmEgeyJwZXJtaXNzaW9ucyI6IFsicGFja2FnZS12aWV3LW1ldHJpY3MiXX0AAAYgoKeXGOOYkcRr8JVMC-_rpFMukq0ACgDPvm0TM9uGGtU"

@featured_blueprint.route("/")
def featured_snaps():
    featured = get_fetaured_snaps()
    return flask.jsonify(featured), 200


@featured_blueprint.route("/", methods=["POST"])
@exchange_required
@login_required
@admin_required
def post_featured_snaps():
    """
    To update the featured snaps:
    3. Update featured snaps to be newly featured
    """
    # minetest DtXxirDGfOc8LeUJVENXGTir4Oq0F7Ts => sondan bir onceki
    # ['wShl4osatuO4sXk2TfzrxE6hZF0biJhS', 'bIb4p4yWWjyZdo2EU64whkZhw9QYYsMH', 'hHiqKR3Bgg6i591bUdkHAzscVywZbpQP', 'wVB1RfBgsZY8dmVifSFeMkTE6UN41osI', 'kvAx1DJUbiqow1LgLfW5OzjksfqUEcqJ', 'ZtF4mLp5Bededu3S65ocO6HfGXCtcvZ9', '6JBjLwyVchga4cOSDqhWJd9NgQfrTYam', 'lfWUNpR7PrPGsDfuxIhVxbj0wZHoH7bK', 'wZo5sef6NuUKCW6DP83fJ6zIZyd5R1sA', 'G9GFr0OFxXrWLDuyfXXD07GFG8UflpJN', 'SfUqQ280Y4bJ0k64qtBKTTXq5ml46tvQ', 'wtlQQaUNASoWxqfxRflcRjU3au6cQ3X0', 'roFhaRzMw8ted6zNEL8NQnNrkFdIHnHv', 'qYBYNvfcQaSWRQAhY89lwrtniZeZMWRH', 'DtXxirDGfOc8LeUJVENXGTir4Oq0F7Ts', 'JbSwFezsVhBG8EpYeNqD4HX31U5WIzdY']
    # new_featured_snaps is the list of featured snaps to be updated
    featured_snaps = flask.request.form.get("snaps")
    if not featured_snaps:
        response = {
            "success": False,
            "message": "Snaps cannot be empty",
        }
        return flask.make_response(response, 500)

    snap_ids = featured_snaps.split(",")
    token = flask.session.get("developer_token")
    if not token:
        return flask.make_response(
            {"success": False, "message": "Missing authentication token"},
            401,
        )
    
     # currently_featured_snap is the list of featured snaps to be deleted
    # currently_featured_snaps = []
    # next = True
    # while next:
    #     featured_snaps = device_gateway.get_featured_snaps()
    #     currently_featured_snaps.extend(
    #         featured_snaps.get("_embedded", {}).get("clickindex:package", [])
    #     )
    #     next = featured_snaps.get("_links", {}).get("next", False)

    # currently_featured_snap_ids = [
    #     snap["snap_id"] for snap in currently_featured_snaps
    # ]

    # delete_response = publisher_gateway.delete_featured_snaps(
    #     token, {"packages": currently_featured_snap_ids}
    # )

    # print(delete_response)

    # if delete_response.status_code != 201:
    #     response = {
    #         "success": False,
    #         "message": "An error occurred while deleting featured snaps",
    #     }
    #     return flask.make_response(response, 500)


    payload = {"packages": snap_ids}
    update_response = publisher_gateway.update_featured_snaps(token, payload)

    if update_response.status_code in (401, 403):
        return flask.make_response(
            {"success": False, "message": "Unauthorized to update featured snaps"},
            update_response.status_code,
        )
    if update_response.status_code != 201:
        return flask.make_response(
            {
                "success": False,
                "message": f"Failed to update featured snaps (status {update_response.status_code})",
            },
            500,
        )

    return flask.make_response({"success": True}, 200)
