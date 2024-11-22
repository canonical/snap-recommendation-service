import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

from collector import collect_initial_snap_data
from filter import filter_snaps_meeting_minimum_criteria
from more_fields import fetch_extra_fields


if __name__ == "__main__":
    collect_initial_snap_data()
    filter_snaps_meeting_minimum_criteria()
    fetch_extra_fields()
