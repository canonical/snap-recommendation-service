from datetime import datetime, timezone

import pytest
from flask import Flask
from sqlalchemy.pool import StaticPool

from snaprecommend import db
from collector.main import featured_selection_due
from collector.schedule import (
    describe_schedule,
    next_occurrence,
    previous_occurrence,
    selection_due,
)
from snaprecommend.settings import set_setting


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    app.config["TESTING"] = True
    app.secret_key = "test"
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_schedule_is_first_monday_of_month():
    # 2026-08-26 is a Wednesday; the first Monday of August 2026 was the 3rd
    # and the next occurrence is 2026-09-07.
    assert previous_occurrence(_utc(2026, 8, 26)) == _utc(2026, 8, 3)
    assert next_occurrence(_utc(2026, 8, 26)) == _utc(2026, 9, 7)


def test_before_first_occurrence_looks_back_a_month():
    # 2026-09-02 is before September's first Monday (the 7th).
    assert previous_occurrence(_utc(2026, 9, 2)) == _utc(2026, 8, 3)


def test_describe_schedule():
    assert describe_schedule() == "first Monday of each month"


def test_due_when_never_run(app):
    assert featured_selection_due() is True


def test_not_due_between_occurrences(app):
    set_setting("featured_last_updated", _utc(2026, 8, 3).isoformat())
    assert selection_due(_utc(2026, 8, 26)) is False


def test_due_after_next_occurrence(app):
    set_setting("featured_last_updated", _utc(2026, 8, 3).isoformat())
    assert selection_due(_utc(2026, 9, 8)) is True


def test_naive_last_updated_is_treated_as_utc(app):
    set_setting("featured_last_updated", datetime(2026, 8, 3).isoformat())
    assert selection_due(_utc(2026, 8, 26)) is False
