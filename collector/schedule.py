"""Scheduling helpers for the featured selection step.

The featured selection runs on a fixed cadence: the first Monday of each
month. This can be made more flexible later if needed.
"""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("collector.schedule")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def describe_schedule() -> str:
    """Return a human readable description of the schedule."""
    return "first Monday of each month"


def _first_monday_of_month(reference: datetime) -> datetime:
    """Return the first Monday of *reference*'s month, at midnight UTC."""
    first = reference.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    return first + timedelta(days=-first.weekday() % 7)


def previous_occurrence(before: datetime | None = None) -> datetime:
    """Return the latest scheduled time at or before *before* (UTC)."""
    now = _as_utc(before or datetime.now(timezone.utc))

    occurrence = _first_monday_of_month(now)
    if occurrence > now:
        previous_month_end = occurrence.replace(day=1) - timedelta(days=1)
        occurrence = _first_monday_of_month(previous_month_end)
    return occurrence


def next_occurrence(after: datetime | None = None) -> datetime:
    """Return the next scheduled time strictly after *after* (UTC)."""
    now = _as_utc(after or datetime.now(timezone.utc))
    previous = previous_occurrence(now)

    next_month = (previous.replace(day=28) + timedelta(days=7)).replace(day=1)
    return _first_monday_of_month(next_month)


def get_last_featured_run() -> datetime | None:
    """Return when the featured selection last completed, if ever."""
    # Imported lazily: snaprecommend imports the collector package at app
    # creation time, so a module-level import would be circular.
    from snaprecommend.settings import get_setting

    setting = get_setting("featured_last_updated")
    if not setting or not setting.value:
        return None
    return _as_utc(datetime.fromisoformat(str(setting.value)))


def selection_due(now: datetime | None = None) -> bool:
    """
    Return whether the featured selection is due to run.

    It is due when a scheduled occurrence has passed since the last recorded
    run, or when it has never run.
    """
    now = _as_utc(now or datetime.now(timezone.utc))
    last_run = get_last_featured_run()
    schedule = describe_schedule()

    if last_run is None:
        logger.info(
            "Featured selection has never run; due now (schedule: %s).",
            schedule,
        )
        return True

    scheduled = previous_occurrence(now)
    due = last_run < scheduled
    logger.info(
        "Featured selection last ran at %s; most recent scheduled run was %s "
        "(schedule: %s). Due: %s",
        last_run,
        scheduled,
        schedule,
        due,
    )
    return due
