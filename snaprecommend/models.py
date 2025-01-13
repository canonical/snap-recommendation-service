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
)
from sqlalchemy.orm import Mapped, mapped_column

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
    revision: Mapped[int] = mapped_column(Integer)  # Latest revision
    links: Mapped[JSON] = mapped_column(JSON)
    media: Mapped[JSON] = mapped_column(JSON)
    developer_validation: Mapped[str] = mapped_column(String)
    license: Mapped[str] = mapped_column(String)
    last_updated: Mapped[datetime] = mapped_column(DateTime)
    active_devices: Mapped[int] = mapped_column(Integer, default=0)
    reaches_min_threshold: Mapped[bool] = mapped_column(Boolean, default=False)


class Scores(db.Model):
    __tablename__: str = "scores"

    snap_id: Mapped[str] = mapped_column(
        String, ForeignKey("snap.snap_id"), primary_key=True
    )

    popularity_score: Mapped[float] = mapped_column(Float)
    recency_score: Mapped[float] = mapped_column(Float)
    trending_score: Mapped[float] = mapped_column(Float)


class Settings(db.Model):
    """
    This table is used to store settings + metadata for the application.
    TODO: This will include the weights for the scoring algorithm eventually
    """

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[JSON] = mapped_column(JSON)
