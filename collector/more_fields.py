from models import Snap
import os
from sqlalchemy.orm import Session
from db import engine
import datetime
import requests
import logging
from dotenv import load_dotenv
from auth import get_auth_header

load_dotenv(override=True)

BATCH_SIZE = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("more_fields")


macroon = os.environ.get("MACAROON")


def batched(iterable, n=1):
    size = len(iterable)
    for idx in range(0, size, n):
        yield iterable[idx : min(idx + n, size)]


releases_url = "http://api.snapcraft.io/api/v1/snaps/search?fields=revision"

metrics_url = "https://dashboard.snapcraft.io/dev/api/snaps/metrics"


def get_number_latest_active_devices(obj):
    """Get the number of latest active devices from the list of
    active devices.

    :returns The number of lastest active devices
    """
    latest_active_devices = 0

    for series_index, series in enumerate(obj["series"]):
        for index, value in enumerate(series["values"]):
            if value is None:
                obj["series"][series_index]["values"][index] = 0
        values = series["values"]
        if len(values) == len(obj["buckets"]):
            # the max of the last 3 values:
            # This is a hack to deal with active devices restting to 0 at
            # the start of the day
            if len(values) >= 3:
                latest_active_devices += max(values[-3:])

    return latest_active_devices


# end time is the current date
end = datetime.datetime.now().strftime("%Y-%m-%d")

# start time is 30 days before the end time
start = datetime.datetime.now() - datetime.timedelta(days=30)
start = start.strftime("%Y-%m-%d")


def get_metrics_for_snaps(snaps: list, session: Session):
    for snaps_batch in batched(snaps, BATCH_SIZE):
        body = {
            "filters": [
                {
                    "start": start,
                    "end": end,
                    "metric_name": "weekly_installed_base_by_version",
                    "snap_id": snap.snap_id,
                }
                for snap in snaps_batch
            ]
        }
        res = requests.post(
            metrics_url,
            headers={
                "Authorization": get_auth_header(macroon),
                "Content-Type": "application/json",
            },
            json=body,
        )
        # TODO: Rate limiting, retry on failure
        if res.status_code != 200:
            logger.error(f"Error fetching metrics: {res.text}")
            error = res.json()
            if (
                error.get("error_list")[0].get("code")
                == "macaroon-needs-refresh"
            ):
                logger.error("Macaroon needs to be refreshed")
                print(
                    "Please look at the README for instructions"
                    "on how to refresh the macaroon"
                )
                break
        else:
            data = res.json()
            for i, snap in enumerate(snaps_batch):
                snap_metrics = data["metrics"][i]
                active_devices = get_number_latest_active_devices(snap_metrics)
                snap.active_devices = active_devices
            session.commit()


def fetch_extra_fields():
    with Session(bind=engine) as session:
        snaps = session.query(Snap).filter(Snap.reaches_min_threshold).all()
        logger.info(f"Fetching active devices for {len(snaps)} snaps")
        get_metrics_for_snaps(snaps, session)


if __name__ == "__main__":
    fetch_extra_fields()
