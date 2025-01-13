import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

MACAROON_ENV_PATH = "FLASK_SNAPSTORE_MACAROON_KEY"

class Config:
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG") or False
    SQLALCHEMY_DATABASE_URI = os.environ.get("POSTGRESQL_DB_CONNECT_STRING")
    SQLALCHEMY_ECHO = os.environ.get("DEBUG") or False
