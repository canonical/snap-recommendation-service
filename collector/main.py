import logging
import sys
import os
from datetime import timedelta, datetime
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
PIPELINE_UPDATE_THRESHOLD = timedelta(hours=12)

INITIAL_STEP_INTERVAL = 1 * 3600   # 1 hour in seconds


def _pipeline_ran_recently() -> bool:
    """Return True if the pipeline completed within PIPELINE_UPDATE_THRESHOLD."""
    last_update = get_setting("last_updated")
    if not last_update:
        return False
    last_update_time = datetime.fromisoformat(str(last_update.value))
    logger.info(f"Last update was at {last_update_time}")
    return datetime.now() - last_update_time < PIPELINE_UPDATE_THRESHOLD


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
        if _pipeline_ran_recently():
            logger.info(
                "Data was updated recently (within %s). Skipping update.",
                PIPELINE_UPDATE_THRESHOLD,
            )
            return
    else:
        logger.info("Force update enabled. updating data.")

    # TODO: don't repeat a step if it has already been done successfully

    collect_initial_snap_data()
    filter_snaps_meeting_minimum_criteria()
    fetch_extra_fields()
    calculate_scores()

    logger.info("Data collection pipeline complete")

    set_setting("last_updated", datetime.now().isoformat())

    db.session.commit()


def collector_service():
    """Run the service with signal handling.

    The initial data collection step runs every hour. The remaining pipeline
    steps (filter, extra_fields, score) run at most once every 12 hours.
    """
    try:
        logger.info("Starting collector service...")
        while True:
            if not os.environ.get(MACAROON_ENV_PATH):
                logger.error("snapstore macaroon secret not given. Quitting")
                return

            logger.info("Running initial data collection step...")
            collect_initial_snap_data()

            # Run the remaining pipeline steps every 12 hours
            run_full_pipeline = not _pipeline_ran_recently()
            if not run_full_pipeline:
                logger.info(
                    "Full pipeline ran recently (within %s). "
                    "Skipping filter, extra_fields and score steps.",
                    PIPELINE_UPDATE_THRESHOLD,
                )

            if run_full_pipeline:
                filter_snaps_meeting_minimum_criteria()
                fetch_extra_fields()
                calculate_scores()
                set_setting("last_updated", datetime.now().isoformat())
                db.session.commit()
                logger.info("Full data collection pipeline complete.")

            logger.info(f"Sleeping for {INITIAL_STEP_INTERVAL} seconds...")
            sleep(INITIAL_STEP_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
