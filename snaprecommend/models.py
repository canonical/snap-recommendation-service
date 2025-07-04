from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column
import enum

from snaprecommend import db

ALL_MEDIA_TYPES: List[str] = ["icon", "screenshot", "video", "banner", "logo"]


class Snap(db.Model):
    __tablename__: str = "snap"

    snap_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    publisher: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(Integer)
    links: Mapped[JSON] = mapped_column(JSON)
    media: Mapped[JSON] = mapped_column(JSON)
    developer_validation: Mapped[str] = mapped_column(String)
    license: Mapped[str] = mapped_column(String)
    last_updated: Mapped[datetime] = mapped_column(DateTime)
    active_devices: Mapped[int] = mapped_column(Integer, default=0)
    reaches_min_threshold: Mapped[bool] = mapped_column(Boolean, default=False)


class RecommendationCategory(db.Model):
    """
    This table is used to store recommendation categories.
    """

    id: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # This is the slug, e.g. 'popularity', 'recent', 'trending'
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)


class SnapRecommendationScore(db.Model):
    """
    This table is used to store the current scores for each snap.
    """

    snap_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("snap.snap_id", ondelete="CASCADE"),
        primary_key=True,
    )
    category: Mapped[str] = mapped_column(
        String,
        ForeignKey("recommendation_category.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[float] = mapped_column(Float)
    exclude: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )


class SnapRecommendationScoreHistory(db.Model):
    """
    This table is used to store the historical data for scores for each snap.
    """

    snap_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("snap.snap_id", ondelete="CASCADE"),
        primary_key=True,
    )
    category: Mapped[str] = mapped_column(
        String,
        ForeignKey("recommendation_category.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[float] = mapped_column(Float)
    exclude: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, primary_key=True
    )


class EditorialSlice(db.Model):
    """
    This table is used to store editorial slices.
    Editorial slices are hand-picked collections of snaps.
    """

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)


class EditorialSliceSnap(db.Model):
    """
    This table is used to store the snaps that are part of each editorial slice.
    """

    editorial_slice_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("editorial_slice.id", ondelete="CASCADE"),
        primary_key=True,
    )
    snap_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("snap.snap_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )


class Settings(db.Model):
    """
    This table is used to store site wide settings + metadata for the application.
    """

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[JSON] = mapped_column(JSON)


class PipelineSteps(enum.Enum):
    COLLECT = "collect"
    FILTER = "filter"
    EXTRA_FIELDS = "extra_fields"
    SCORE = "score"


class PipelineStepLog(db.Model):
    """
    This table is used to store the status of each step in the pipeline.
    """

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    step: Mapped[PipelineSteps] = mapped_column(Enum(PipelineSteps))
    success: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
