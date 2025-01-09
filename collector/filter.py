from sqlalchemy import func
from app.models import Snap
import datetime
from app import db

import logging

logger = logging.getLogger("collector")


# TODO: It would be nice to have the criteria configured through UI.
# i.e, consider having a config table in the database
MINIMUM_DESCRIPTION_LENGTH = 50
LAST_UPDATED_THRESHOLD = 180  # in days
MINIMUM_MEDIA_ITEMS = 1  # Including the icon


def snap_meets_minimum_criteria_query():
    """
    Builds the SQL filter criteria for snaps meeting the minimum requirements
    to be considered for recommendations
    """
    update_threshold = datetime.datetime.now() - datetime.timedelta(
        days=LAST_UPDATED_THRESHOLD
    )

    has_icon = Snap.icon.isnot(None)

    has_media = func.json_array_length(Snap.media) >= MINIMUM_MEDIA_ITEMS

    issues = func.json_extract_path(Snap.links, "issues")
    has_issues_link = issues.isnot(None) & (func.json_array_length(issues) > 0)

    contact = func.json_extract_path(Snap.links, "contact")
    has_contact_link = contact.isnot(None) & (
        func.json_array_length(contact) > 0
    )

    author_can_be_reached = has_issues_link | has_contact_link

    has_description = Snap.description.isnot(None) & (
        func.length(Snap.description) > MINIMUM_DESCRIPTION_LENGTH
    )

    is_recent = Snap.last_updated > update_threshold

    return (
        has_icon,
        has_media,
        author_can_be_reached,
        has_description,
        is_recent,
    )


def filter_snaps_meeting_minimum_criteria():
    query = db.session.query(Snap).filter(*snap_meets_minimum_criteria_query())

    db.session.query(Snap).update(
        {Snap.reaches_min_threshold: False}, synchronize_session=False
    )

    query.update({Snap.reaches_min_threshold: True}, synchronize_session=False)

    db.session.commit()

    snap_count = query.count()
    logger.info(f"Found {snap_count} snaps meeting minimum criteria.")


if __name__ == "__main__":
    filter_snaps_meeting_minimum_criteria()
