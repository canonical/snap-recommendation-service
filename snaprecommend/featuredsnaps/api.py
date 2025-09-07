import flask

from snaprecommend.featuredsnaps.utils import get_fetaured_snaps, get_packages
from snaprecommend.auth.session import device_gateway,publisher_gateway, dashboard
from snaprecommend.auth.decorators import login_required, exchange_required, admin_required

featured_blueprint = flask.Blueprint("featured", __name__)


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
    In this view, we do three things:
    1. Fetch all currently featured snaps
    2. Delete the currently featured snaps
    3. Update featured snaps to be newly featured
    """
    # new_featured_snaps is the list of featured snaps to be updated
    featured_snaps = flask.request.form.get("snaps")
    if not featured_snaps:
        response = {
            "success": False,
            "message": "Snaps cannot be empty",
        }
        return flask.make_response(response, 500)
    new_featured_snaps = featured_snaps.split(",")

    # currently_featured_snap is the list of featured snaps to be deleted
    currently_featured_snaps = []
    next = True
    while next:
        featured_snaps = device_gateway.get_featured_snaps()
        currently_featured_snaps.extend(
            featured_snaps.get("_embedded", {}).get("clickindex:package", [])
        )
        next = featured_snaps.get("_links", {}).get("next", False)

    currently_featured_snap_ids = [
        snap["snap_id"] for snap in currently_featured_snaps
    ]

    delete_response = publisher_gateway.delete_featured_snaps(
        flask.session["exchanged_developer_token"], {"packages": currently_featured_snap_ids}
    )

    if delete_response.status_code != 201:
        response = {
            "success": False,
            "message": "An error occurred while deleting featured snaps",
        }
        return flask.make_response(response, 500)
    snap_ids = [
        dashboard.get_snap_id(flask.session, snap_name)
        for snap_name in new_featured_snaps
    ]

    payload = {"packages": snap_ids}
    update_response = publisher_gateway.update_featured_snaps(
        flask.session["exchanged_developer_token"], payload
    )

    if update_response.status_code != 201:
        response = {
            "success": False,
            "message": "An error occured while updating featured snaps",
        }
        return flask.make_response(response, 500)

    return flask.make_response({"success": True}, 200)


FIELDS = [
    "title",
    "summary",
    "media",
    "publisher",
    "categories",
]


@featured_blueprint.route("store.json")
def get_store_packages():
    args = dict(flask.request.args)

    res = flask.make_response(get_packages(FIELDS, 15, args))
    return res