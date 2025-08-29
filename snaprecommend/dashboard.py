from flask import (
    Blueprint,
    request,
    redirect,
    jsonify,
)
from snaprecommend.sso import login_required
from snaprecommend.logic import exclude_snap_from_category

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@login_required
def dashboard():
    return redirect("/v2/dashboard")


@dashboard_blueprint.route("/api/exclude_snap", methods=["POST"])
@login_required
def exclude_snap():
    data = request.get_json()
    snap_id = data.get("snap_id")
    category = data.get("category")
    if snap_id and category:
        exclude_snap_from_category(category, snap_id)
    return jsonify({"status": "success"}), 200
