from flask import Flask, render_template, redirect
from flask_cors import CORS
import datetime
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from snaprecommend.cli import cli_blueprint
from snaprecommend.sso import init_sso, login_required
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

db = SQLAlchemy()
migrate = Migrate()

OLD_PATHS = [
    "excluded_snaps",
    "editorial_slices",
    "settings",
]


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)
    app.config.from_prefixed_env()

    init_sso(app)

    app.register_blueprint(cli_blueprint)

    from snaprecommend.api import api_blueprint
    from snaprecommend.dashboard import dashboard_blueprint

    @app.route("/")
    def index():
        return "Snap recommendations API - Copyright 2025 Canonical"

    @app.route("/_status/check")
    def status_check():
        return "OK"

    @app.route("/v2/dashboard")
    @app.route("/v2/dashboard/<path:path>")
    @login_required
    def serve_react_app(path=None):
        if path in OLD_PATHS:
            return redirect(f"/dashboard/{path}")
        return render_template("index.html")

    app.url_map.strict_slashes = False

    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")

    db.init_app(app)
    migrate.init_app(app, db)

    app.logger.setLevel(logging.INFO)

    CORS(app)

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    return app


app = create_app()

scheduler = BackgroundScheduler()


def scheduled_collector():
    from collector.main import collect_data

    with app.app_context():
        try:
            collect_data()
        except Exception as e:
            app.logger.error(f"Error starting scheduled collector: {e}")


# This is a hack to only run the collector scheduler when the server is running
# not when executing CLI commands
def is_running_server():
    import sys

    cli_command = " ".join(sys.argv)
    return "flask run" in cli_command or "gunicorn" in cli_command


if not scheduler.running and is_running_server():
    scheduler.start()
    scheduler.add_job(
        func=scheduled_collector,
        trigger="interval",
        # Run on initialization, and then
        # every 7 days (10 seconds to let the app start)
        start_date=datetime.datetime.now() + datetime.timedelta(seconds=10),
        days=7,
        id="collect_data",
    )
