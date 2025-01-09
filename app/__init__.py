from flask import Flask
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from app.cli import cli_blueprint

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

    app.register_blueprint(cli_blueprint)

    from app.api import api_blueprint

    app.register_blueprint(api_blueprint)

    db.init_app(app)

    migrate.init_app(app, db)

    app.logger.setLevel(logging.INFO)

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    return app
