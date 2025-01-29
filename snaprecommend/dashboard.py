from flask import Blueprint, render_template
from snaprecommend.sso import login_required
from snaprecommend.logic import get_category_top_snaps

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
