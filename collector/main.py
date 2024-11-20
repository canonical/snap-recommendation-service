import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

from collector import collect_initial_snap_data
from process import process_snaps_meeting_min_criteria
from more_fields import fetch_extra_fields


if __name__ == "__main__":
    collect_initial_snap_data()
    process_snaps_meeting_min_criteria()
    fetch_extra_fields()
