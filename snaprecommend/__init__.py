from flask import Flask, render_template
from flask_cors import CORS
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from snaprecommend.cli import cli_blueprint
from snaprecommend.auth.decorators import dashboard_login, exchange_required, admin_required
from snaprecommend.auth.sso import init_sso

from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)
    app.config.from_prefixed_env()
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    init_sso(app)

    app.register_blueprint(cli_blueprint)

    from snaprecommend.api import api_blueprint
    from snaprecommend.dashboard import dashboard_blueprint

    @app.route("/")
    def index():
        return "Snap recommendations API - Copyright 2025 Canonical~!"

    @app.route("/_status/check")
    def status_check():
        return "OK!"

    @app.route("/v2/dashboard/featuredsnaps")
    @exchange_required
    @admin_required
    @dashboard_login
    def serve_featured_snaps():
        return render_template("index.html")

    @app.route("/v2/dashboard")
    @app.route("/v2/dashboard/<path:path>")
    @dashboard_login
    def serve_react_app(path=None):
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
