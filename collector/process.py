from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models import Snap, ALL_MEDIA_TYPES
import datetime

from db import engine


def snap_meets_minimum_criteria_query():
    """Builds the SQL filter criteria for snaps meeting the minimum requirements."""
    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)

    # Check if `media` and `links` are non-empty JSON fields
    return (
        func.json_array_length(Snap.media)
        > 0,  # Ensure media exists and has items
        Snap.description.isnot(None),
        func.length(Snap.description) > 0,
        Snap.contact.isnot(None),
        func.length(Snap.contact) > 0,
        Snap.last_updated > six_months_ago,
    )


def calculate_media_score_query():
    """Defines a SQL expression to calculate the media score."""
    return func.least(func.json_array_length(Snap.media), 5) * (
        func.cardinality(
            func.array(
                func.json_extract_path_text(
                    Snap.media, "type"
                )  # Assuming JSON field contains 'type'
            )
        )
        / len(ALL_MEDIA_TYPES)
    )


def calculate_links_score_query():
    """Defines a SQL expression to calculate the links score."""
    return func.sum(
        case(
            [
                (func.length(Snap.links[key]) > 0, 1)
                for key in Snap.links.keys()
            ],
            else_=0,
        )
    )


def calculate_metadata_score_query():
    """Defines a SQL expression to calculate the metadata score."""
    return (
        case([(Snap.description.isnot(None), 1)], else_=0)
        + case([(Snap.license.isnot(None), 1)], else_=0)
        + case([(Snap.website.isnot(None), 1)], else_=0)
        + case([(Snap.contact.isnot(None), 1)], else_=0)
        + calculate_links_score_query()
        + calculate_media_score_query()
    )


def calculate_dev_score_query():
    """Calculates developer validation score based on validation status."""
    return case(
        [
            (Snap.developer_validation == "starred", 2),
            (Snap.developer_validation == "verified", 1),
        ],
        else_=0,
    )


def process_snaps_meeting_min_criteria():
    with Session(bind=engine) as session:
        snaps_meeting_criteria_query = session.query(Snap).filter(
            *snap_meets_minimum_criteria_query()
        )

        snaps_meeting_criteria_query.update(
            {
                Snap.reaches_min_threshold: True,
            },
        )

        session.commit()

        print(
            f"Snaps meeting criteria updated: {snaps_meeting_criteria_query.count()}"
        )
