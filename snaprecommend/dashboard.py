from flask import Blueprint, render_template
from snaprecommend.sso import login_required
from snaprecommend.logic import get_top_snaps_by_field

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@login_required
def dashboard():
    limit = 20

    popular_snaps = get_top_snaps_by_field("popularity_score", limit=limit)
    recent_snaps = get_top_snaps_by_field("recency_score", limit=limit)
    trending_snaps = get_top_snaps_by_field("trending_score", limit=limit)

    context = {
        "popular_snaps": popular_snaps,
        "recent_snaps": recent_snaps,
        "trending_snaps": trending_snaps,
    }

    return render_template("dashboard.html", **context)
