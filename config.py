import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

MACAROON_ENV_PATH = "FLASK_SNAPSTORE_MACAROON_KEY"


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("POSTGRESQL_DB_CONNECT_STRING")
    SQLALCHEMY_ECHO = os.environ.get("FLASK_DEBUG_DB") or False
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
