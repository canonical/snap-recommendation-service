from models import Snap
import os
from sqlalchemy.orm import Session
from db import init_db
import datetime
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("collector")

engine = init_db()


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


def get_metrics_for_snaps(snaps: list):
    session = Session(bind=engine)
    for snaps_batch in batched(snaps, 20):
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
                "Authorization": macroon,
                "Content-Type": "application/json",
            },
            json=body,
        )
        if res.status_code != 200:
            logger.error(f"Error fetching metrics: {res.text}")
        else:
            data = res.json()
            devices_by_snap = {}
            for i, snap in enumerate(snaps_batch):
                snap_metrics = data["metrics"][i]
                active_devices = get_number_latest_active_devices(snap_metrics)
                devices_by_snap[snap.snap_id] = active_devices
            # update the database with the active devices
            for snap in snaps_batch:
                snap.active_devices = devices_by_snap.get(snap.snap_id, 0)
            session.commit()
            logger.info(f"Updated active devices for {len(snaps_batch)} snaps")


if __name__ == "__main__":
    # do this for all snaps in db
    with Session(bind=engine) as session:

        snaps = session.query(Snap).filter(Snap.reaches_min_threshold).all()
        logger.info(f"Fetching active devices for {len(snaps)} snaps")
        get_metrics_for_snaps(snaps)
