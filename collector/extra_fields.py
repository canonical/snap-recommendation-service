from snaprecommend.models import Snap
from sqlalchemy.orm import Session
from collector.auth import get_auth_header
import datetime
import requests
import logging
import os
from typing import List
from snaprecommend import db
from config import MACAROON_ENV_PATH


BATCH_SIZE = 15
RELEASES_URL = "http://api.snapcraft.io/api/v1/snaps/search?fields=revision"
METRICS_URL = "https://dashboard.snapcraft.io/dev/api/snaps/metrics"
MACAROON = os.environ.get(MACAROON_ENV_PATH)

logger = logging.getLogger("extra_fields")


def batched(iterable: list, batch_size: int = 1):
    """
    Yields successive chunks of a specified size from the input iterable.
    """
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


def calculate_latest_active_devices(metrics_data: dict) -> int:
    """
    Calculates the latest number of active devices from metrics data.
    """
    latest_active_devices = 0
    metrics_data["series"] = sorted(
        metrics_data["series"], key=lambda x: x["name"]
    )

    for series_index, series in enumerate(metrics_data["series"]):
        for index, value in enumerate(series["values"]):
            if value is None:
                metrics_data["series"][series_index]["values"][index] = 0
        values = series["values"]
        if len(values) == len(metrics_data["buckets"]):
            for i in range(len(values) - 1, -1, -1):
                if values[i] != 0:
                    latest_active_devices += values[i]
                    break

    return latest_active_devices


def fetch_metrics_from_api(
    snaps: List[Snap], start_date: str, end_date: str
) -> dict:
    """
    Fetches metrics data for a batch of snaps from the API.
    """
    request_body = {
        "filters": [
            {
                "start": start_date,
                "end": end_date,
                "metric_name": "weekly_installed_base_by_version",
                "snap_id": snap.snap_id,
            }
            for snap in snaps
        ]
    }

    try:
        response = requests.post(
            METRICS_URL,
            headers={
                "Authorization": get_auth_header(MACAROON),
                "Content-Type": "application/json",
            },
            json=request_body,
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as http_err:
        if http_err.response.status_code == 401:
            logger.error(
                "Authentication error. Check your macaroon. "
                "More details in the README."
            )
            logger.error(http_err.response.text)
            raise SystemExit
        logger.error(f"HTTP error occurred: {http_err}")
        raise

    except requests.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred during API call: {e}")
        raise


def process_and_update_snap_metrics(
    snaps: List[Snap], metrics_data: dict, db_session: Session
):
    """
    Processes API response data and updates
    the database with active device counts.
    """
    try:
        for snap, snap_metrics in zip(snaps, metrics_data.get("metrics", [])):
            active_devices = calculate_latest_active_devices(snap_metrics)
            snap.active_devices = active_devices
        db_session.commit()
        logger.info(f"Updated metrics for {len(snaps)} snaps successfully.")
    except KeyError as key_err:
        logger.error(f"Missing expected data in metrics response: {key_err}")
    except Exception as ex:
        logger.error(f"Unexpected error during metrics processing: {ex}")


def fetch_and_update_metrics_for_snaps(snaps: List[Snap], db_session: Session):
    """
    Fetches and updates metrics for a list of snaps in batches.
    """
    start_date, end_date = get_metrics_time_range()
    for snap_batch in batched(snaps, BATCH_SIZE):
        try:
            metrics_data = fetch_metrics_from_api(
                snap_batch, start_date, end_date
            )
            process_and_update_snap_metrics(
                snap_batch, metrics_data, db_session
            )
        except Exception as ex:
            logger.error(f"Failed to process batch of snaps: {ex}")


def get_metrics_time_range() -> tuple[str, str]:
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)

    end_date = (yesterday).strftime("%Y-%m-%d")
    start_date = (yesterday - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return start_date, end_date


def fetch_eligible_snaps(db_session: Session) -> List[Snap]:
    """
    Fetches snaps from the database that meet the minimum threshold.
    """
    try:
        snaps = db_session.query(Snap).filter(Snap.reaches_min_threshold).all()
        logger.info(
            f"Found {len(snaps)} eligible snaps for metrics collection."
        )
        return snaps
    except Exception as e:
        logger.error(f"Error querying eligible snaps: {e}")
        raise


def update_snap_metrics():
    try:
        eligible_snaps = fetch_eligible_snaps(db.session)
        fetch_and_update_metrics_for_snaps(eligible_snaps, db.session)
    except Exception as e:
        logger.error(f"Error during metrics update process: {e}")
        raise


def fetch_extra_fields():
    # Might add more fields in the future
    update_snap_metrics()
