from flask import Blueprint, render_template, request, redirect, url_for, flash
from snaprecommend.sso import login_required
from snaprecommend.logic import (
    get_category_top_snaps,
    exclude_snap_from_category,
    include_snap_in_category,
    get_all_categories,
    get_category_excluded_snaps,
)
from snaprecommend.editorials import (
    get_all_editorial_slices,
    create_editorial_slice,
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


@dashboard_blueprint.route("/editorial_slices")
@login_required
def editorial_slices():
    slices = get_all_editorial_slices()

    context = {
        "editorial_slices": slices,
    }

    return render_template("editorial_slices.html", **context)


@dashboard_blueprint.route("/editorial_slice", methods=["POST"])
@login_required
def create_slice():
    name = request.form.get("name")
    description = request.form.get("description")

    try:
        create_editorial_slice(name, description)
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("dashboard.editorial_slices"))


@dashboard_blueprint.route("/excluded_snaps")
@login_required
def excluded_snaps():

    excluded_snaps = []

    for category in get_all_categories():
        excluded_snaps.append(
            {
                "category": category,
                "snaps": get_category_excluded_snaps(category.id),
            }
        )

    context = {
        "excluded_snaps": excluded_snaps,
    }
    return render_template("excluded_snaps.html", **context)


@dashboard_blueprint.route("/exclude_snap", methods=["POST"])
@login_required
def exclude_snap():
    snap_id = request.form.get("snap_id")
    category = request.form.get("category")
    if snap_id and category:
        exclude_snap_from_category(category, snap_id)
    return redirect(url_for("dashboard.dashboard"))


@dashboard_blueprint.route("/include_snap", methods=["POST"])
@login_required
def include_snap():
    snap_id = request.form.get("snap_id")
    category = request.form.get("category")
    if snap_id and category:
        include_snap_in_category(category, snap_id)
    return redirect(request.referrer)
