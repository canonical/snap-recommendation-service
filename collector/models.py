from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Snap(Base):
    __tablename__: str = "snap"

    snap_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    publisher: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(Integer)  # Latest revision
    links: Mapped[str] = mapped_column(String)
    media: Mapped[str] = mapped_column(String)
    developer_validation: Mapped[str] = mapped_column(String)
    license: Mapped[str] = mapped_column(String)
    last_updated: Mapped[datetime] = mapped_column(DateTime)
    active_devices: Mapped[int] = mapped_column(Integer, default=0)
    reaches_min_threshold: Mapped[bool] = mapped_column(Boolean, default=False)


class Scores(Base):
    __tablename__: str = "scores"

    snap_id: Mapped[str] = mapped_column(
        String, ForeignKey("snap.snap_id"), primary_key=True
    )
    popularity_score: Mapped[int] = mapped_column(Integer)
    recency_score: Mapped[int] = mapped_column(Integer)
    trending_score: Mapped[int] = mapped_column(Integer)


ALL_MEDIA_TYPES: List[str] = ["icon", "screenshot", "video", "banner", "logo"]
