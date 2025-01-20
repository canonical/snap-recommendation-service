from flask import Flask
import datetime
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from snaprecommend.cli import cli_blueprint
from snaprecommend.sso import init_sso
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(
        __name__,
    )
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

    app.register_blueprint(api_blueprint, url_prefix="/api")

    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")

    db.init_app(app)

    migrate.init_app(app, db)

    app.logger.setLevel(logging.INFO)

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    return app


scheduler = BackgroundScheduler()


def scheduled_collector():
    from collector.main import collect_data

    app = create_app()
    with app.app_context():
        try:
            collect_data()
        except Exception as e:
            app.logger.error(f"Error starting scheduled collector: {e}")


scheduler.add_job(
    func=scheduled_collector,
    trigger="interval",
    # Run on initialization, and then
    # every 7 days (10 seconds to let the app start)
    start_date=datetime.datetime.now() + datetime.timedelta(seconds=10),
    days=7,
    id="collect_data",
)

scheduler.start()
