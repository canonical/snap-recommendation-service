from flask import Blueprint

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.route("/")
def dashboard():
    return "Dashboard goes here!"
