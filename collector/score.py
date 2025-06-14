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


def calculate_category_scores(category: str):
    """Calculate the scores for all recommendable snaps in a category."""

    session = db.session

    filter_condition = Snap.reaches_min_threshold.is_(True)

    min_active_devices, max_active_devices = normalize_field(
        session, Snap.active_devices, filter_condition=filter_condition
    )
    min_last_updated, max_last_updated = normalize_field(
        session, Snap.last_updated, filter_condition=filter_condition
    )

    scores_to_insert = []

    snaps = session.query(Snap).filter(filter_condition).all()

    for snaps_batch in batched(snaps, 100):
        for snap in snaps_batch:
            # Normalize fields with log scaling for active devices
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

            # TODO: formula will be a field in category eventually
            if category == "popular":
                score = calculate_popularity_score(
                    active_devices_normalized, metadata_score, dev_score
                )
            elif category == "recent":
                score = calculate_recency_score(
                    last_updated_normalized, metadata_score, dev_score
                )
            elif category == "trending":
                score = calculate_trending_score(
                    last_updated_normalized,
                    active_devices_normalized,
                    metadata_score,
                    dev_score,
                )
            else:
                raise ValueError(f"Invalid category: {category}")

            scores_to_insert.append(
                {"snap_id": snap.snap_id, "category": category, "score": score}
            )

        if scores_to_insert:
            stmt = insert(SnapRecommendationScore).values(scores_to_insert)
            update_stmt = stmt.on_conflict_do_update(
                index_elements=["snap_id", "category"],
                set_={"score": stmt.excluded.score},
            )
            session.execute(update_stmt)
            session.commit()


def calculate_scores():
    """Calculate the scores for all recommendable snaps."""

    try:

        migrate_old_scores()

        calculate_category_scores("popular")
        calculate_category_scores("recent")
        calculate_category_scores("trending")

        add_pipeline_step_log(PipelineSteps.SCORE, True)
    except Exception as e:
        add_pipeline_step_log(PipelineSteps.SCORE, False, str(e))
        raise


def migrate_old_scores():
    """Migrate old scores to the history table."""
    session = db.session

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

    session.commit()
