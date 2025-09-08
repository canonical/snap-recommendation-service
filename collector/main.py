import logging
import sys
import os
from datetime import  timedelta, datetime
from time import sleep
from collector.collect import collect_initial_snap_data
from collector.filter import filter_snaps_meeting_minimum_criteria
from collector.extra_fields import fetch_extra_fields
from collector.score import calculate_scores
from snaprecommend import db
from config import MACAROON_ENV_PATH
from snaprecommend.settings import get_setting, set_setting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("collector")


# TODO: This should be a setting
DATA_UPDATE_THRESHOLD = timedelta(days=7)

FETCH_INTERVAL = 24 * 3600  # 24 hours in seconds

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
        last_update = get_setting("last_updated")
        if last_update:
            last_update_time = datetime.fromisoformat(str(last_update.value))
            logger.info(f"Last update was at {last_update_time}")
            time_since_last_update = datetime.now() - last_update_time

            if time_since_last_update < DATA_UPDATE_THRESHOLD:
                logger.info(
                    "Data was updated recently (within %s days). Skipping update.",
                    DATA_UPDATE_THRESHOLD.days,
                )
                return
    else:
        logger.info("Force update enabled. updating data.")

    # TODO: if a step fails, the pipeline should not continue
    # TODO: don't repeat a step if it has already been done successfully

    collect_initial_snap_data()
    filter_snaps_meeting_minimum_criteria()
    fetch_extra_fields()
    calculate_scores()

    logger.info("Data collection pipeline complete")

    set_setting("last_updated", datetime.now().isoformat())

    db.session.commit()





def collector_service():
    """Run the service with signal handling."""
    try:
        logger.info("Starting collector service...")
        while True:
            collect_data()
            logger.info(f"Sleeping for {FETCH_INTERVAL} seconds...")
            sleep(FETCH_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)