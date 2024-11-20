import sqlalchemy
import logging
from models import Snap

# create a new logger for the db module
logger = logging.getLogger(__name__)


def init_db():
    engine = sqlalchemy.create_engine(
        "sqlite:///../db.sqlite", echo=logger.isEnabledFor(logging.DEBUG)
    )

    Snap.metadata.create_all(engine)

    logger.info("Database initialized")
    return engine


engine = init_db()
