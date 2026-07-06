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

FEATURED_UPDATE_INTERVAL_DEFAULT = 30  # days

INITIAL_STEP_INTERVAL = 1 * 3600   # 1 hour in seconds


def _pipeline_ran_recently() -> bool:
    """Return True if the pipeline completed within PIPELINE_UPDATE_THRESHOLD."""
    last_update = get_setting("last_updated")
    if not last_update:
        return False
    last_update_time = datetime.fromisoformat(str(last_update.value))
    logger.info(f"Last update was at {last_update_time}")
    return datetime.now() - last_update_time < PIPELINE_UPDATE_THRESHOLD


def _featured_ran_recently() -> bool:
    """
    Return True if the automated featured selection ran within the configured
    interval (default 30 days, overridable via the featured_update_interval_days
    setting in the Settings table).
    """
    last = get_setting("featured_last_updated")
    if not last or not last.value:
        return False
    interval_setting = get_setting("featured_update_interval_days")
    interval_days = (
        int(interval_setting.value)
        if interval_setting and interval_setting.value is not None
        else FEATURED_UPDATE_INTERVAL_DEFAULT
    )
    last_time = datetime.fromisoformat(str(last.value))
    delta = timedelta(days=interval_days)
    logger.info(
        "Featured snaps last updated at %s (interval: %d days).",
        last_time,
        interval_days,
    )
    return datetime.utcnow() - last_time < delta


def collect_data(force_update: bool = False, force_featured: bool = False):
    """
    Main function to run the data collection pipeline.
    By default, this function will check if the data was updated
    within the threshold before running the pipeline. If the data
    is up to date, the pipeline will be skipped.

    Args:
        force_update (bool): If True, bypass the last update check and update.
        force_featured (bool): If True, run featured selection even if it ran recently.
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

    # Featured selection runs on its own monthly cadence, independent of the
    # daily pipeline. It is deliberately *not* guarded by force_update so a
    # forced pipeline re-run doesn't inadvertently repeat a monthly refresh.
    if force_featured or not _featured_ran_recently():
        logger.info("Running automated featured snap selection.")
        try:
            from collector.featured_selector import select_featured_snaps
            select_featured_snaps()
        except Exception as exc:
            # Selection failure is logged and notified inside select_featured_snaps;
            # it must not abort the rest of the pipeline.
            logger.error("Featured selection failed (pipeline continues): %s", exc)
    else:
        logger.info(
            "Featured snaps were updated recently. Skipping selection this run."
        )


def collector_service():
    """Run the service with signal handling.

    The initial data collection step runs every hour. The remaining pipeline
    steps (filter, extra_fields, score) run at most once every 12 hours.
    The featured selection step runs at most once per configured interval
    (default 30 days).
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

                # Featured selection runs after a complete pipeline, subject to
                # its own monthly cadence.
                if not _featured_ran_recently():
                    logger.info("Running automated featured snap selection.")
                    try:
                        from collector.featured_selector import select_featured_snaps
                        select_featured_snaps()
                    except Exception as exc:
                        logger.error(
                            "Featured selection failed (service continues): %s", exc
                        )
                else:
                    logger.info(
                        "Featured snaps updated recently. Skipping selection."
                    )

            logger.info(f"Sleeping for {INITIAL_STEP_INTERVAL} seconds...")
            sleep(INITIAL_STEP_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
