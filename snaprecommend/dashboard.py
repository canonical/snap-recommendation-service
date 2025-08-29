from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app,
    jsonify,
)
from snaprecommend.models import PipelineSteps
from snaprecommend.sso import login_required
from snaprecommend.logic import (
    exclude_snap_from_category,
    get_most_recent_pipeline_step_logs,
)
from snaprecommend.settings import get_setting
import threading

from collector.main import (
    collect_initial_snap_data,
    filter_snaps_meeting_minimum_criteria,
    fetch_extra_fields,
    calculate_scores,
)


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


