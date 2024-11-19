from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class Snap(Base):
    __tablename__ = "snap"
    snap_id = mapped_column(String, primary_key=True)
    title = mapped_column(String)
    name = mapped_column(String)
    version = mapped_column(String)
    summary = mapped_column(String)
    description = mapped_column(String)
    website = mapped_column(String, nullable=True)
    contact = mapped_column(String, nullable=True)
    publisher = mapped_column(String)
    revision = mapped_column(Integer)
    links = mapped_column(String)
    media = mapped_column(String)
    developer_validation = mapped_column(String)
    license = mapped_column(String)
    last_updated = mapped_column(DateTime)
    active_devices = mapped_column(Integer, default=0)
    reaches_min_threshold = mapped_column(Boolean, default=False)


ALL_MEDIA_TYPES = ["icon", "screenshot", "video", "banner", "logo"]
