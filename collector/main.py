import logging

from collector.collect import collect_initial_snap_data
from collector.filter import filter_snaps_meeting_minimum_criteria
from collector.more_fields import fetch_extra_fields
from collector.score import calculate_scores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


if __name__ == "__main__":
    collect_initial_snap_data()
    filter_snaps_meeting_minimum_criteria()
    fetch_extra_fields()
    calculate_scores()
