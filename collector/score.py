from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from snaprecommend.models import Snap, Scores, ALL_MEDIA_TYPES
from sqlalchemy.dialects.postgresql import insert
from snaprecommend import db


def normalize_field(session: Session, field: str, filter_condition=None):
    query = session.query(func.min(field), func.max(field))
    if filter_condition is not None:
        query = query.filter(filter_condition)
    return query.one()


def calculate_media_score(snap: Snap):
    """Calculate the media quality score for a snap."""

    media_types = [item["type"] for item in snap.media]
    media_counter = Counter(media_types)

    return sum(media_counter[media_type] for media_type in ALL_MEDIA_TYPES) / (
        len(ALL_MEDIA_TYPES) * 2
    )


def calculate_metadata_score(snap: Snap):
    """Calculate the metadata quality score for a snap."""
    # only count non empty links
    num_of_links = min(
        5, sum(1 for link in snap.links.values() if link)
    )  # max 5 links
    set_license = snap.license != "unset"
    media_quality = calculate_media_score(snap)
    links_quality = (set_license + num_of_links) / 6

    return (media_quality + links_quality) / 2


def calculate_dev_score(snap: Snap):
    """Calculate the developer score for a snap."""
    score = 0
    if snap.developer_validation == "starred":
        score = 2
    elif snap.developer_validation == "verified":
        score = 1
    return score / 2


def calculate_popularity_score(
    active_devices_normalized, metadata_score, dev_score
):
    """Calculate the popularity score for a snap."""
    return (
        active_devices_normalized * 0.5
        + metadata_score * 0.3
        + dev_score * 0.2
    )


def calculate_recency_score(
    last_updated_normalized, metadata_score, dev_score
):
    """Calculate the recency score for a snap."""
    return (
        last_updated_normalized * 0.5 + metadata_score * 0.3 + dev_score * 0.2
    )


def calculate_trending_score(
    active_devices_normalized, metadata_score, dev_score
):
    """Calculate the trending score for a snap."""
    return (
        active_devices_normalized * 0.5
        + metadata_score * 0.3
        + dev_score * 0.2
    )


def calculate_scores():
    """Calculate the scores for all recommendable snaps."""

    session = db.session

    clear_old_scores(session)

    filter_condition = Snap.reaches_min_threshold.is_(True)

    min_active_devices, max_active_devices = normalize_field(
        session, Snap.active_devices, filter_condition=filter_condition
    )
    min_last_updated, max_last_updated = normalize_field(
        session, Snap.last_updated, filter_condition=filter_condition
    )

    scores_to_insert = []

    snaps = session.query(Snap).filter(filter_condition).all()

    for snap in snaps:
        # Normalize fields
        active_devices_normalized = (
            (snap.active_devices - min_active_devices)
            / (max_active_devices - min_active_devices)
            if max_active_devices != min_active_devices
            else 1
        )
        last_updated_normalized = (
            (snap.last_updated - min_last_updated).total_seconds()
            / (max_last_updated - min_last_updated).total_seconds()
            if max_last_updated != min_last_updated
            else 1
        )

        metadata_score = calculate_metadata_score(snap)
        dev_score = calculate_dev_score(snap)

        popularity_score = calculate_popularity_score(
            active_devices_normalized, metadata_score, dev_score
        )
        recency_score = calculate_recency_score(
            last_updated_normalized, metadata_score, dev_score
        )
        trending_score = calculate_trending_score(
            active_devices_normalized, metadata_score, dev_score
        )

        scores_to_insert.append(
            {
                "snap_id": snap.snap_id,
                "popularity_score": popularity_score,
                "recency_score": recency_score,
                "trending_score": trending_score,
            }
        )

    if scores_to_insert:
        insert_stmt = insert(Scores).values(scores_to_insert)
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["snap_id"],
            set_={
                "popularity_score": insert_stmt.excluded.popularity_score,
                "recency_score": insert_stmt.excluded.recency_score,
                "trending_score": insert_stmt.excluded.trending_score,
            },
        )
        session.execute(update_stmt)
        session.commit()


def clear_old_scores(session):
    """Clear old scores from the database."""
    session.query(Scores).delete()
    session.commit()
