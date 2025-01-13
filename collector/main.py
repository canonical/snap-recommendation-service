import logging
import os

from datetime import timedelta, datetime
from collector.collect import collect_initial_snap_data
from collector.filter import filter_snaps_meeting_minimum_criteria
from collector.extra_fields import fetch_extra_fields
from collector.score import calculate_scores
from snaprecommend.models import Settings
from snaprecommend import db
from config import MACAROON_ENV_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("collector")

# TODO: This should be a setting
DATA_UPDATE_THRESHOLD = timedelta(days=7)


def collect_data(force_update: bool = False):
    """
    Main function to run the data collection pipeline.
    By default, this function will check if the data was updated
    within the threshold before running the pipeline. If the data
    is up to date, the pipeline will be skipped.

    Args:
        force_update (bool): If True, bypass the last update check and update.
    """
    logger.info("Starting data collection pipeline")

    if not os.environ.get(MACAROON_ENV_PATH):
        logger.error("snapstore macaroon secret not given. Quitting")
        return

    if not force_update:

        last_update = Settings.query.filter_by(key="last_updated").first()

        if last_update:

            last_update_time = datetime.fromisoformat(last_update.value)
            time_since_last_update = datetime.now() - last_update_time

            if time_since_last_update < DATA_UPDATE_THRESHOLD:
                logger.info(
                    "Data was updated recently (within %s days). Skipping update.",
                    DATA_UPDATE_THRESHOLD.days,
                )
                return
    else:
        logger.info("Force update enabled. updating data.")

    collect_initial_snap_data()
    filter_snaps_meeting_minimum_criteria()
    fetch_extra_fields()
    calculate_scores()

    logger.info("Data collection pipeline complete")
    last_update = Settings.query.filter_by(key="last_updated").first()

    current_time = datetime.now().isoformat()

    if last_update:
        last_update.value = current_time
    else:
        last_update = Settings(key="last_updated", value=current_time)
        db.session.add(last_update)

    db.session.commit()
