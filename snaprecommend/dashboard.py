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
    get_snap_by_name,
    get_most_recent_pipeline_step_logs,
)
from snaprecommend.editorials import (
    get_all_editorial_slices,
    get_editorial_slice_with_snaps,
    create_editorial_slice,
    delete_editorial_slice,
    add_snap_to_editorial_slice,
    remove_snap_from_editorial_slice,
    update_editorial_slice,
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


@dashboard_blueprint.route("/settings")
@login_required
def settings():
    pipeline_steps = get_most_recent_pipeline_step_logs()

    last_updated = get_setting("last_updated")

    if last_updated.value:
        last_updated = datetime.fromisoformat(last_updated.value)

    context = {
        "pipeline_steps": pipeline_steps,
        "last_updated": last_updated,
    }

    return render_template("settings.html", **context)


@dashboard_blueprint.route("/run_pipeline_step", methods=["POST"])
@login_required
def run_pipeline_step():
    step_name = request.args.get("step_name")
    if not step_name:
        abort(400, "Step name is required")

    steps_map = {
        PipelineSteps.COLLECT.value: collect_initial_snap_data,
        PipelineSteps.FILTER.value: filter_snaps_meeting_minimum_criteria,
        PipelineSteps.EXTRA_FIELDS.value: fetch_extra_fields,
        PipelineSteps.SCORE.value: calculate_scores,
    }

    if step_name not in steps_map:
        abort(400, "Invalid step name")

    step_function = steps_map[step_name]

    def run_step(app_context):
        app_context.push()
        step_function()

    threading.Thread(
        target=run_step,
        args=(current_app.app_context(),),
    ).start()

    # TODO: tmp fix until we add "in_progress" to steps
    flash(
        f"Pipeline step '{step_name}' started, please don't trigger again until last run time is updated",
        "success",
    )

    return redirect(url_for("dashboard.settings"))
