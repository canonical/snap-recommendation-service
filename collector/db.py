import sqlalchemy
import logging
from models import Snap
import os

# create a new logger for the db module
logger = logging.getLogger("db")


def init_db():
    connection_string = os.getenv("POSTGRESQL_DB_CONNECT_STRING")
    if not connection_string:
        logger.error("POSTGRESQL_DB_CONNECT_STRING is not set")
        raise SystemExit(1)

    engine = sqlalchemy.create_engine(
        connection_string, echo=logger.isEnabledFor(logging.DEBUG)
    )

    Snap.metadata.create_all(engine)

    logger.info("Database initialized")
    return engine


engine = init_db()
