from flask import Blueprint, render_template, request, redirect, url_for
from snaprecommend.sso import login_required
from snaprecommend.logic import (
    get_category_top_snaps,
    exclude_snap_from_category,
    get_all_categories,
)

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@login_required
def dashboard():
    limit = 20

    popular_snaps = get_category_top_snaps("popular", limit=limit)
    recent_snaps = get_category_top_snaps("recent", limit=limit)
    trending_snaps = get_category_top_snaps("trending", limit=limit)

    context = {
        "popular_snaps": popular_snaps,
        "recent_snaps": recent_snaps,
        "trending_snaps": trending_snaps,
    }

    return render_template("dashboard.html", **context)
@dashboard_blueprint.route("/exclude_snap", methods=["POST"])
@login_required
def exclude_snap():
    snap_id = request.form.get("snap_id")
    category = request.form.get("category")
    if snap_id and category:
        exclude_snap_from_category(category, snap_id)
    return redirect(url_for("dashboard.dashboard"))
