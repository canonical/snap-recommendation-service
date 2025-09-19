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
