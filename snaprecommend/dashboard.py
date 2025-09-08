from flask import (
    Blueprint,
    redirect,
)
from snaprecommend.auth.decorators import login_required


dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@login_required
def dashboard():
    return redirect("/v2/dashboard")
