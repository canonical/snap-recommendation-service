from flask import Flask
from flask_cors import CORS
import datetime
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from snaprecommend.cli import cli_blueprint
from snaprecommend.sso import init_sso
from apscheduler.schedulers.background import BackgroundScheduler
from flask import send_from_directory, render_template
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder="templates")
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
    
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react_app(path):
        static_file_path = os.path.join(app.static_folder, path)
        if path != "" and os.path.exists(static_file_path):
            return send_from_directory(app.static_folder, path)
        return render_template("index.html")

    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")

    db.init_app(app)
    migrate.init_app(app, db)

    app.logger.setLevel(logging.INFO)

    # init cors manually (add header)
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
