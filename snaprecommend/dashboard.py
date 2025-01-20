from flask import Blueprint
from snaprecommend.sso import login_required

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
@login_required
def dashboard():
    return "Dashboard goes here!"
