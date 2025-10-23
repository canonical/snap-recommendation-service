from flask import (
    Blueprint,
    redirect,
)
from snaprecommend.auth.decorators import dashboard_login


dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@dashboard_login
def dashboard():
    return redirect("/v2/dashboard")
