from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from snaprecommend.models import (
    Snap,
    SnapRecommendationScore,
    SnapRecommendationScoreHistory,
    ALL_MEDIA_TYPES,
    PipelineSteps,
)
from sqlalchemy.dialects.postgresql import insert
from snaprecommend import db
from collector.extra_fields import batched
import math
from snaprecommend.logic import add_pipeline_step_log
import logging

logger = logging.getLogger("scorer")


def normalize_field(session: Session, field: str, filter_condition=None):
    query = session.query(func.min(field), func.max(field))
    if filter_condition is not None:
        query = query.filter(filter_condition)
    return query.one()


def log_scale(value, min_value, max_value):
    """Apply log scaling to a value, ensuring the result is between 0 and 1."""
    if value <= 0:
        return 0

    log_min = math.log1p(min_value)  # log(1 + min_value)
    log_max = math.log1p(max_value)  # log(1 + max_value)
    log_value = math.log1p(value)  # log(1 + value)

    if log_max == log_min:
        return 1  # Avoid division by zero, treat as uniform scaling

    return (log_value - log_min) / (log_max - log_min)


def calculate_media_score(snap: Snap):
    """Calculate the media quality score for a snap."""

    media_types = [item["type"] for item in snap.media]
    media_counter = Counter(media_types)

    return sum(media_counter[media_type] for media_type in ALL_MEDIA_TYPES) / (
        len(ALL_MEDIA_TYPES) * 2
    )


def calculate_metadata_score(snap: Snap):
    """Calculate the metadata quality score for a snap."""
    MAX_LINKS = 5
    num_of_links = min(
        MAX_LINKS, sum(1 for link in snap.links.values() if link)
    )
    set_license = snap.license != "unset"
    media_quality = min(1.0, calculate_media_score(snap))  # Clamp to max 1.0
    links_quality = (set_license + num_of_links) / (
        MAX_LINKS + 1
    )  # max 6 (5 links + license)
    return (media_quality + links_quality) / 2


def calculate_dev_score(snap: Snap):
    """Calculate the developer score for a snap."""
    score = 0
    if snap.developer_validation in ["verified", "starred"]:
        score = 1
    return score


def calculate_popularity_score(
    active_devices_normalized, metadata_score, dev_score
):
    """Calculate the popularity score for a snap."""
    return (
        active_devices_normalized * 0.7
        + metadata_score * 0.1
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
    last_updated_normalized,
    active_devices_normalized,
    metadata_score,
    dev_score,
):
    """Calculate the trending score for a snap."""
    return (
        last_updated_normalized * 0.25
        + active_devices_normalized * 0.25
        + metadata_score * 0.3
        + dev_score * 0.2
    )


def calculate_top_rated_score(rating, metadata_score, dev_score):
    """Calculate the top-rated score for a snap."""
    return rating * 0.8 + metadata_score * 0.1 + dev_score * 0.1


def calculate_category_scores():
    """Calculate scores with balanced category assignment.
    This function calculates scores for each snap in four categories:
    popular, recent, trending, and top-rated. It then assigns snaps to
    categories such that each snap is assigned to the category with
    the highest score. This prevents overlap across categories and
    keeps a uniform distribution.
    """

    session = db.session

    filter_condition = Snap.reaches_min_threshold.is_(True)

    min_active_devices, max_active_devices = normalize_field(
        session, Snap.active_devices, filter_condition=filter_condition
    )
    min_last_updated, max_last_updated = normalize_field(
        session, Snap.last_updated, filter_condition=filter_condition
    )

    snaps = session.query(Snap).filter(filter_condition).all()

    snap_scores = []
    for snap in snaps:
        active_devices_normalized = log_scale(
            snap.active_devices, min_active_devices, max_active_devices
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
            last_updated_normalized,
            active_devices_normalized,
            metadata_score,
            dev_score,
        )
        top_rated_score = calculate_top_rated_score(
            snap.raw_rating or 0, metadata_score, dev_score
        )

        snap_scores.append(
            {
                "snap_id": snap.snap_id,
                "popular": popularity_score,
                "recent": recency_score,
                "trending": trending_score,
                "top_rated": top_rated_score,
            }
        )

    assigned_snaps = set()
    scores_to_insert = []

    # Calculate how many snaps per category (balanced distribution)
    total_snaps = len(snap_scores)
    snaps_per_category = total_snaps // 4  # 4 categories

    logger.info(
        f"Assigning {snaps_per_category} snaps per category from "
        f"{total_snaps} total snaps"
    )

    categories = ["popular", "recent", "trending", "top_rated"]

    for category in categories:
        sorted_snaps = sorted(
            snap_scores, key=lambda x: x[category], reverse=True
        )

        assigned_count = 0
        for snap_data in sorted_snaps:
            if (
                snap_data["snap_id"] not in assigned_snaps
                and assigned_count < snaps_per_category
            ):
                scores_to_insert.append(
                    {
                        "snap_id": snap_data["snap_id"],
                        "category": category,
                        "score": snap_data[category],
                    }
                )
                assigned_snaps.add(snap_data["snap_id"])
                assigned_count += 1

    for snap_data in snap_scores:
        if snap_data["snap_id"] not in assigned_snaps:
            scores = {
                "popular": snap_data["popular"],
                "recent": snap_data["recent"],
                "trending": snap_data["trending"],
                "top_rated": snap_data["top_rated"],
            }
            best_category = max(scores, key=scores.get)
            scores_to_insert.append(
                {
                    "snap_id": snap_data["snap_id"],
                    "category": best_category,
                    "score": scores[best_category],
                }
            )

    for scores_batch in batched(scores_to_insert, 100):
        if scores_batch:
            stmt = insert(SnapRecommendationScore).values(scores_batch)
            session.execute(stmt)
            session.commit()

    logger.info(f"Assigned {len(scores_to_insert)} snaps across categories")


def calculate_scores():
    """Calculate scores with exclusive assignment to prevent overlap."""

    try:
        delete_old_scores()
        migrate_current_scores()

        clear_current_scores()

        calculate_category_scores()

        add_pipeline_step_log(PipelineSteps.SCORE, True)
    except Exception as e:
        add_pipeline_step_log(PipelineSteps.SCORE, False, str(e))
        raise


def delete_old_scores():
    """Delete old scores from the history table."""
    session = db.session
    logger.info("Deleting old scores from history table")

    cutoff_date = datetime.now() - timedelta(days=90)
    deleted = (
        session.query(SnapRecommendationScoreHistory)
        .filter(SnapRecommendationScoreHistory.created_at < cutoff_date)
        .delete()
    )

    logger.info(f"Deleted {deleted} old scores from history table")

    session.commit()


def migrate_current_scores():
    """Migrate old scores to the history table."""
    session = db.session
    logger.info("Migrating current scores to history table")

    scores = session.query(SnapRecommendationScore).all()

    scores_to_insert = [
        {
            "snap_id": score.snap_id,
            "category": score.category,
            "created_at": score.created_at,
            "exclude": score.exclude,
            "score": score.score,
        }
        for score in scores
    ]

    if scores_to_insert:
        stmt = insert(SnapRecommendationScoreHistory).values(scores_to_insert)
        stmt = stmt.on_conflict_do_nothing()
        session.execute(stmt)
        session.commit()

    logger.info(
        f"Migrated {len(scores_to_insert)} current scores to history table"
    )

    session.commit()


def clear_current_scores():
    """Clear all current scores to prepare for exclusive assignment."""
    session = db.session
    logger.info("Clearing all current scores")

    deleted = session.query(SnapRecommendationScore).delete()
    logger.info(f"Cleared {deleted} current scores")

    session.commit()
